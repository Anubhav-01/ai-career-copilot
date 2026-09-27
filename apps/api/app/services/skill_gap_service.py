"""Skill-gap analysis: resume skills vs job requirements.

Priorities:
    critical      - required skill, no related resume skill at all
    important     - required skill, resume has a same-category neighbor
    nice_to_have  - preferred skill that is missing

Gaps are derived purely from extracted (evidence-backed) skills - the
system never infers skills the user did not demonstrate.
"""
import uuid

from sqlalchemy.orm import Session

from app.ai.parsing.skills import normalize_skill, skill_category
from app.core.errors import NotFoundError, ValidationFailedError
from app.models.match import SkillGap
from app.models.user import User
from app.repositories.job import JobRepository
from app.repositories.match import MatchRepository
from app.repositories.resume import ResumeRepository
from app.schemas.job import JobAnalysis


class SkillGapService:
    def __init__(self, db: Session):
        self.db = db
        self.matches = MatchRepository(db)
        self.resumes = ResumeRepository(db)
        self.jobs = JobRepository(db)

    def analyze(self, user: User, resume_id: uuid.UUID, job_id: uuid.UUID) -> list[SkillGap]:
        resume = self.resumes.get_for_user(resume_id, user.id)
        if resume is None:
            raise NotFoundError("Resume not found.")
        if resume.status != "completed":
            raise ValidationFailedError("Resume has not finished processing.")
        job = self.jobs.get_for_user(job_id, user.id)
        if job is None or job.analysis is None:
            raise NotFoundError("Job not found or not analyzed.")

        analysis = JobAnalysis.model_validate(job.analysis)
        resume_skills = {s.normalized for s in resume.skills}
        resume_categories = {s.category for s in resume.skills if s.category}

        gaps: list[SkillGap] = []
        seen: set[str] = set()

        for skill in analysis.required_skills:
            canonical = normalize_skill(skill)
            if canonical in resume_skills or canonical in seen:
                continue
            seen.add(canonical)
            category = skill_category(canonical)
            related = category in resume_categories if category else False
            gaps.append(SkillGap(
                user_id=user.id, resume_id=resume.id, job_id=job.id,
                skill=skill, normalized=canonical,
                priority="important" if related else "critical",
                reason=(
                    f"Required by '{job.title}'. You have related"
                    f" {category.replace('_', ' ')} skills, so this should be"
                    " fast to pick up."
                    if related and category
                    else f"Required by '{job.title}' and no related skill was"
                         " found on your resume."
                ),
            ))

        for skill in analysis.preferred_skills:
            canonical = normalize_skill(skill)
            if canonical in resume_skills or canonical in seen:
                continue
            seen.add(canonical)
            gaps.append(SkillGap(
                user_id=user.id, resume_id=resume.id, job_id=job.id,
                skill=skill, normalized=canonical,
                priority="nice_to_have",
                reason=f"Listed as preferred (not required) for '{job.title}'.",
            ))

        return self.matches.replace_gaps_for_job(user.id, resume.id, job.id, gaps)

    def list_gaps(self, user: User) -> list[SkillGap]:
        return self.matches.gaps_for_user(user.id)
