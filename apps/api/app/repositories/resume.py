import uuid

from app.models.resume import Resume, ResumeAnalysis, ResumeSection, ResumeSkill
from app.repositories.base import BaseRepository


class ResumeRepository(BaseRepository[Resume]):
    model = Resume

    def replace_skills(self, resume_id: uuid.UUID, skills: list[dict]) -> None:
        self.db.query(ResumeSkill).filter(ResumeSkill.resume_id == resume_id).delete()
        for skill in skills:
            self.db.add(ResumeSkill(resume_id=resume_id, **skill))
        self.db.flush()

    def replace_sections(self, resume_id: uuid.UUID, sections: list[dict]) -> None:
        self.db.query(ResumeSection).filter(
            ResumeSection.resume_id == resume_id
        ).delete()
        for section in sections:
            self.db.add(ResumeSection(resume_id=resume_id, **section))
        self.db.flush()

    def add_analysis(self, analysis: ResumeAnalysis) -> ResumeAnalysis:
        self.db.add(analysis)
        self.db.flush()
        return analysis

    def latest_analysis(self, resume_id: uuid.UUID) -> ResumeAnalysis | None:
        return (
            self.db.query(ResumeAnalysis)
            .filter(ResumeAnalysis.resume_id == resume_id)
            .order_by(ResumeAnalysis.created_at.desc())
            .first()
        )

    def analyses_for_user(self, user_id: uuid.UUID) -> list[ResumeAnalysis]:
        return (
            self.db.query(ResumeAnalysis)
            .join(Resume, Resume.id == ResumeAnalysis.resume_id)
            .filter(Resume.user_id == user_id, Resume.deleted_at.is_(None))
            .order_by(ResumeAnalysis.created_at.asc())
            .all()
        )

    def skills_for_user(self, user_id: uuid.UUID) -> list[ResumeSkill]:
        return (
            self.db.query(ResumeSkill)
            .join(Resume, Resume.id == ResumeSkill.resume_id)
            .filter(Resume.user_id == user_id, Resume.deleted_at.is_(None))
            .all()
        )

    def count(self) -> int:
        return self.db.query(Resume).filter(Resume.deleted_at.is_(None)).count()
