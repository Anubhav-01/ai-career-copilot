"""Resume workflows: upload, background processing (parse -> skills ->
sections -> RAG indexing), analysis, bullet improvement and tailoring."""
import time
import uuid
from pathlib import Path

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.ai.embeddings.factory import get_embedding_provider
from app.ai.guardrails import call_structured
from app.ai.llm.factory import get_llm_provider
from app.ai.parsing.extract_text import extract_text, validate_upload
from app.ai.parsing.resume_parser import parse_resume, split_sections
from app.ai.parsing.skills import extract_skills
from app.ai.prompts import SYSTEMS, build_prompt
from app.ai.rag.indexer import index_document
from app.ai.scoring.resume_score import compute_resume_score
from app.core.cache import get_cache
from app.core.config import get_settings
from app.core.errors import AIServiceError, NotFoundError, ValidationFailedError
from app.core.logging import get_logger, log_event
from app.core.security import generate_secure_filename
from app.models.resume import Resume, ResumeAnalysis
from app.models.user import User
from app.repositories.audit import AuditRepository
from app.repositories.job import JobRepository
from app.repositories.resume import ResumeRepository
from app.repositories.user import UserRepository
from app.schemas.resume import (
    BulletImprovement,
    ResumeExtraction,
    TailoringSuggestion,
)

logger = get_logger(__name__)


class ExplanationOnly(BaseModel):
    """Schema for explanation-only LLM calls."""

    explanation: str = ""


class ResumeService:
    def __init__(self, db: Session):
        self.db = db
        self.resumes = ResumeRepository(db)
        self.audit = AuditRepository(db)

    # --- upload -----------------------------------------------------------

    def upload(self, user: User, filename: str, content: bytes, title: str | None) -> Resume:
        settings = get_settings()
        ext = validate_upload(filename, content, settings.max_upload_size_bytes)

        upload_dir = Path(settings.upload_dir) / str(user.id)
        upload_dir.mkdir(parents=True, exist_ok=True)
        storage_name = generate_secure_filename(filename)
        storage_path = upload_dir / storage_name
        storage_path.write_bytes(content)

        resume = self.resumes.add(Resume(
            user_id=user.id,
            title=title or filename.rsplit(".", 1)[0][:255],
            original_filename=filename[:255],
            storage_path=str(storage_path),
            file_type=ext,
            status="pending",
        ))
        self.audit.log("resume.upload", user_id=user.id,
                       resource_type="resume", resource_id=str(resume.id))
        return resume

    # --- background processing pipeline ------------------------------------

    def process(self, resume_id: uuid.UUID) -> None:
        """Runs in a background task: extract -> parse -> persist -> index."""
        started = time.perf_counter()
        resume = self.resumes.get(resume_id)
        if resume is None:
            return
        resume.status = "processing"
        self.db.flush()
        try:
            content = Path(resume.storage_path).read_bytes()
            text = extract_text(content, resume.file_type)
            extraction = parse_resume(text, get_llm_provider())

            resume.raw_text = text
            resume.parsed = extraction.model_dump()

            skills = extract_skills(text)
            self.resumes.replace_skills(resume.id, [
                {
                    "name": s.name, "normalized": s.normalized,
                    "category": s.category, "evidence": s.evidence,
                    "source": "deterministic",
                }
                for s in skills
            ])
            self.resumes.replace_sections(resume.id, [
                {
                    "section_type": section, "title": section.title(),
                    "content": content_block, "order_index": index,
                }
                for index, (section, content_block) in enumerate(split_sections(text).items())
            ])
            index_document(
                self.db, get_embedding_provider(), resume.user_id,
                resume.id, "resume", text,
            )
            resume.status = "completed"
            resume.error_message = None
            elapsed = time.perf_counter() - started
            self._record_processing_time(elapsed)
            log_event(logger, "resume_processed", latency_ms=round(elapsed * 1000))
        except Exception as exc:  # noqa: BLE001 - background task boundary
            resume.status = "failed"
            resume.error_message = getattr(exc, "message", "Processing failed.")
            log_event(logger, "resume_processing_failed", error=type(exc).__name__)
        finally:
            self.db.commit()

    @staticmethod
    def _record_processing_time(seconds: float) -> None:
        cache = get_cache()
        stats = cache.get("metrics:resume_processing") or {"count": 0, "total": 0.0}
        stats["count"] += 1
        stats["total"] += seconds
        cache.set("metrics:resume_processing", stats)

    # --- analysis -----------------------------------------------------------

    def analyze(self, user: User, resume_id: uuid.UUID) -> ResumeAnalysis:
        resume = self._get_completed(user, resume_id)
        extraction = ResumeExtraction.model_validate(resume.parsed or {})
        profile = UserRepository(self.db).get_profile(user.id)
        target_roles = list(profile.target_roles or []) if profile else []

        overall, components, ats, recommendations = compute_resume_score(
            resume.raw_text or "", extraction, target_roles
        )

        explanation = self._explain_score(components)
        settings = get_settings()
        analysis = self.resumes.add_analysis(ResumeAnalysis(
            resume_id=resume.id,
            overall_score=overall,
            scores={"components": [c.model_dump() for c in components]},
            ats=ats.model_dump(),
            recommendations=[r.model_dump() for r in recommendations],
            explanation=explanation,
            weights=settings.resume_score_weights.model_dump(),
        ))
        get_cache().delete_prefix(f"dashboard:{user.id}")
        self.audit.log("resume.analyze", user_id=user.id,
                       resource_type="resume", resource_id=str(resume.id))
        return analysis

    def _explain_score(self, components) -> str | None:
        prompt = build_prompt(
            instruction="Explain this resume score to the user in 3-4 plain"
                        " sentences, naming the weakest areas.",
            context={"scores": [c.model_dump() for c in components]},
            schema_hint='{"explanation": string}',
        )
        try:
            result = call_structured(
                get_llm_provider(), "resume_explanation",
                SYSTEMS["resume_explanation"], prompt,
                ExplanationOnly, max_tokens=400,
            )
            return result.explanation or None
        except AIServiceError:
            return None

    # --- bullet improvement ---------------------------------------------------

    def improve_bullet(self, user: User, resume_id: uuid.UUID, bullet: str,
                       target_role: str | None) -> BulletImprovement:
        resume = self._get_completed(user, resume_id)
        if bullet.lower() not in (resume.raw_text or "").lower():
            raise ValidationFailedError(
                "That bullet was not found in this resume. Select text exactly"
                " as it appears."
            )
        prompt = build_prompt(
            instruction=(
                "Rewrite this resume bullet to be stronger (action verb first,"
                " concise, professional). Keep ALL facts identical. If a metric"
                " is missing, set missing_metric_suggestion to tell the user"
                " where a real number would help - never invent one."
            ),
            context={"bullet": bullet, "target_role": target_role or ""},
            schema_hint="{original, improved, rationale, missing_metric_suggestion}",
        )
        result = call_structured(
            get_llm_provider(), "bullet_improvement",
            SYSTEMS["bullet_improvement"], prompt, BulletImprovement, max_tokens=500,
        )
        result.original = bullet
        return result

    # --- tailoring -------------------------------------------------------------

    def tailor(self, user: User, resume_id: uuid.UUID, job_id: uuid.UUID) -> TailoringSuggestion:
        resume = self._get_completed(user, resume_id)
        job = JobRepository(self.db).get_for_user(job_id, user.id)
        if job is None or job.analysis is None:
            raise NotFoundError("Job not found or not analyzed yet.")

        resume_skills = {s.normalized for s in resume.skills}
        job_analysis = job.analysis
        required = job_analysis.get("required_skills", [])
        preferred = job_analysis.get("preferred_skills", [])
        matched = [s for s in required + preferred if s.lower() in
                   {r.lower() for r in resume_skills}]
        missing = [s for s in required if s.lower() not in
                   {r.lower() for r in resume_skills}]
        weak_bullets = [
            b for e in (resume.parsed or {}).get("experience", [])
            for b in e.get("bullets", [])
            if not any(ch.isdigit() for ch in b)
        ][:5]

        prompt = build_prompt(
            instruction=(
                "Suggest how to tailor this resume for the job. Only reference"
                " skills in matched_skills as strengths. For missing_skills,"
                " tell the user to add them ONLY if they truthfully have the"
                " experience. Never fabricate experience."
            ),
            context={
                "matched_skills": matched, "missing_skills": missing,
                "job_keywords": job_analysis.get("keywords", []),
                "weak_bullets": weak_bullets,
                "job_title": job.title,
            },
            schema_hint=("{skills_to_emphasize[], keywords_to_include[],"
                         " sections_to_modify[], bullets_to_improve[],"
                         " missing_evidence[], summary}"),
        )
        return call_structured(
            get_llm_provider(), "tailoring", SYSTEMS["tailoring"], prompt,
            TailoringSuggestion, max_tokens=900,
        )

    # --- helpers -----------------------------------------------------------------

    def get_owned(self, user: User, resume_id: uuid.UUID) -> Resume:
        resume = self.resumes.get_for_user(resume_id, user.id)
        if resume is None:
            raise NotFoundError("Resume not found.")
        return resume

    def _get_completed(self, user: User, resume_id: uuid.UUID) -> Resume:
        resume = self.get_owned(user, resume_id)
        if resume.status != "completed":
            raise ValidationFailedError(
                f"Resume is not ready (status: {resume.status})."
            )
        return resume

    def delete(self, user: User, resume_id: uuid.UUID) -> None:
        resume = self.get_owned(user, resume_id)
        self.resumes.soft_delete(resume)
        try:
            Path(resume.storage_path).unlink(missing_ok=True)
        except OSError:
            logger.warning("Failed to remove stored resume file")
        get_cache().delete_prefix(f"dashboard:{user.id}")
        self.audit.log("resume.delete", user_id=user.id,
                       resource_type="resume", resource_id=str(resume_id))
