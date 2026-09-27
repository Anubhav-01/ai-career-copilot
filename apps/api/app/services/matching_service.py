"""Semantic + hybrid job matching with full explainability."""
import re
import uuid

from sqlalchemy.orm import Session

from app.ai.embeddings.factory import get_embedding_provider
from app.ai.guardrails import call_structured
from app.ai.llm.factory import get_llm_provider
from app.ai.prompts import SYSTEMS, build_prompt
from app.ai.rag.retriever import Retriever
from app.ai.scoring.match_score import ResumeSkillInfo, compute_match
from app.core.cache import get_cache
from app.core.errors import AIServiceError, NotFoundError, ValidationFailedError
from app.models.match import JobMatch
from app.models.user import User
from app.repositories.audit import AuditRepository
from app.repositories.job import JobRepository
from app.repositories.match import MatchRepository
from app.repositories.resume import ResumeRepository
from app.repositories.user import UserRepository
from app.schemas.job import JobAnalysis
from app.services.resume_service import ExplanationOnly

_YEAR_RANGE_RE = re.compile(r"(20\d{2}|19\d{2})")


class MatchingService:
    def __init__(self, db: Session):
        self.db = db
        self.matches = MatchRepository(db)
        self.resumes = ResumeRepository(db)
        self.jobs = JobRepository(db)
        self.audit = AuditRepository(db)

    def match(self, user: User, job_id: uuid.UUID, resume_id: uuid.UUID) -> JobMatch:
        job = self.jobs.get_for_user(job_id, user.id)
        if job is None or job.analysis is None:
            raise NotFoundError("Job not found or not analyzed.")
        resume = self.resumes.get_for_user(resume_id, user.id)
        if resume is None:
            raise NotFoundError("Resume not found.")
        if resume.status != "completed":
            raise ValidationFailedError("Resume has not finished processing.")

        retriever = Retriever(self.db, get_embedding_provider())
        semantic = retriever.document_similarity(user.id, resume.id, job.id)

        analysis = JobAnalysis.model_validate(job.analysis)
        skill_infos = [
            ResumeSkillInfo(name=s.normalized, category=s.category, evidence=s.evidence)
            for s in resume.skills
        ]
        result = compute_match(
            job_analysis=analysis,
            resume_skills=skill_infos,
            resume_text=resume.raw_text or "",
            semantic_similarity=semantic,
            candidate_years=self._estimate_years(user, resume),
            has_degree=bool((resume.parsed or {}).get("education")),
        )

        explanation = self._explain(result)
        match = self.matches.add(JobMatch(
            user_id=user.id, resume_id=resume.id, job_id=job.id,
            overall_score=result.overall,
            components=result.components.model_dump(),
            strong_matches=result.strong_matches,
            partial_matches=result.partial_matches,
            missing_skills=result.missing_skills,
            evidence=[e.model_dump() for e in result.evidence],
            explanation=explanation,
            weights=result.weights,
        ))
        get_cache().delete_prefix(f"dashboard:{user.id}")
        self.audit.log("job.match", user_id=user.id,
                       resource_type="job", resource_id=str(job.id))
        return match

    def _estimate_years(self, user: User, resume) -> float | None:
        """Prefer explicit profile value; otherwise estimate from resume
        experience date ranges (conservative)."""
        profile = UserRepository(self.db).get_profile(user.id)
        if profile and profile.experience_years is not None:
            return float(profile.experience_years)
        experience = (resume.parsed or {}).get("experience", [])
        years: list[int] = []
        for entry in experience:
            for field in ("start_date", "end_date"):
                value = entry.get(field) or ""
                years.extend(int(y) for y in _YEAR_RANGE_RE.findall(value))
        if len(years) >= 2:
            return float(max(years) - min(years))
        return None

    def _explain(self, result) -> str | None:
        prompt = build_prompt(
            instruction="Explain this job match score in 2-4 sentences.",
            context={
                "overall": result.overall,
                "components": result.components.model_dump(),
                "strong_matches": result.strong_matches,
                "missing_skills": result.missing_skills,
            },
            schema_hint='{"explanation": string}',
        )
        try:
            return call_structured(
                get_llm_provider(), "match_explanation",
                SYSTEMS["match_explanation"], prompt, ExplanationOnly,
                max_tokens=300,
            ).explanation or None
        except AIServiceError:
            return None
