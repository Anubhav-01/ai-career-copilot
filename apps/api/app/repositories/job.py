import uuid

from app.models.job import Job, JobSkill
from app.repositories.base import BaseRepository


class JobRepository(BaseRepository[Job]):
    model = Job

    def replace_skills(self, job_id: uuid.UUID, skills: list[dict]) -> None:
        self.db.query(JobSkill).filter(JobSkill.job_id == job_id).delete()
        for skill in skills:
            self.db.add(JobSkill(job_id=job_id, **skill))
        self.db.flush()

    def count(self) -> int:
        return self.db.query(Job).filter(Job.deleted_at.is_(None)).count()
