"""Job description workflows: analysis (hybrid), storage, RAG indexing.

Job analyses are cached by content hash - re-analyzing an identical
description costs zero LLM calls (cost control).
"""
import hashlib
import uuid

from sqlalchemy.orm import Session

from app.ai.embeddings.factory import get_embedding_provider
from app.ai.llm.factory import get_llm_provider
from app.ai.parsing.jd_parser import analyze_job
from app.ai.parsing.skills import normalize_skill, skill_category
from app.ai.rag.indexer import index_document
from app.core.cache import get_cache
from app.core.errors import NotFoundError
from app.models.job import Job
from app.models.user import User
from app.repositories.audit import AuditRepository
from app.repositories.job import JobRepository
from app.schemas.job import JobAnalysis, JobAnalyzeRequest


class JobService:
    def __init__(self, db: Session):
        self.db = db
        self.jobs = JobRepository(db)
        self.audit = AuditRepository(db)

    def analyze_and_store(self, user: User, payload: JobAnalyzeRequest) -> Job:
        cache = get_cache()
        content_hash = hashlib.sha256(payload.description.encode()).hexdigest()
        cached = cache.get(f"job_analysis:{content_hash}")

        if cached is not None:
            analysis = JobAnalysis.model_validate(cached)
        else:
            analysis = analyze_job(
                payload.description, get_llm_provider(),
                title=payload.title, company=payload.company,
            )
            cache.set(f"job_analysis:{content_hash}", analysis.model_dump(),
                      ttl_seconds=3600)

        job = self.jobs.add(Job(
            user_id=user.id,
            title=payload.title or analysis.job_title or "Untitled role",
            company=payload.company or analysis.company or None,
            location=payload.location,
            source_url=payload.source_url,
            description_text=payload.description,
            analysis=analysis.model_dump(),
        ))
        self.jobs.replace_skills(job.id, [
            {
                "name": s, "normalized": normalize_skill(s),
                "kind": kind, "category": skill_category(normalize_skill(s)),
            }
            for kind, skills in (
                ("required", analysis.required_skills),
                ("preferred", analysis.preferred_skills),
            )
            for s in skills
        ])
        index_document(
            self.db, get_embedding_provider(), user.id, job.id, "job",
            payload.description,
        )
        get_cache().delete_prefix(f"dashboard:{user.id}")
        self.audit.log("job.analyze", user_id=user.id,
                       resource_type="job", resource_id=str(job.id))
        return job

    def get_owned(self, user: User, job_id: uuid.UUID) -> Job:
        job = self.jobs.get_for_user(job_id, user.id)
        if job is None:
            raise NotFoundError("Job not found.")
        return job

    def delete(self, user: User, job_id: uuid.UUID) -> None:
        job = self.get_owned(user, job_id)
        self.jobs.soft_delete(job)
        get_cache().delete_prefix(f"dashboard:{user.id}")
