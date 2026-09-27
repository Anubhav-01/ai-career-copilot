import uuid

from sqlalchemy.orm import Session

from app.models.match import JobMatch, LearningRoadmap, SkillGap


class MatchRepository:
    def __init__(self, db: Session):
        self.db = db

    def add(self, match: JobMatch) -> JobMatch:
        self.db.add(match)
        self.db.flush()
        return match

    def latest_for_pair(
        self, user_id: uuid.UUID, resume_id: uuid.UUID, job_id: uuid.UUID
    ) -> JobMatch | None:
        return (
            self.db.query(JobMatch)
            .filter(
                JobMatch.user_id == user_id,
                JobMatch.resume_id == resume_id,
                JobMatch.job_id == job_id,
            )
            .order_by(JobMatch.created_at.desc())
            .first()
        )

    def list_for_user(self, user_id: uuid.UUID) -> list[JobMatch]:
        return (
            self.db.query(JobMatch)
            .filter(JobMatch.user_id == user_id)
            .order_by(JobMatch.created_at.desc())
            .all()
        )

    def count(self) -> int:
        return self.db.query(JobMatch).count()

    # --- skill gaps ---

    def replace_gaps_for_job(
        self, user_id: uuid.UUID, resume_id: uuid.UUID, job_id: uuid.UUID | None,
        gaps: list[SkillGap],
    ) -> list[SkillGap]:
        query = self.db.query(SkillGap).filter(
            SkillGap.user_id == user_id, SkillGap.resume_id == resume_id
        )
        if job_id is None:
            query = query.filter(SkillGap.job_id.is_(None))
        else:
            query = query.filter(SkillGap.job_id == job_id)
        query.delete()
        for gap in gaps:
            self.db.add(gap)
        self.db.flush()
        return gaps

    def gaps_for_user(self, user_id: uuid.UUID) -> list[SkillGap]:
        return (
            self.db.query(SkillGap)
            .filter(SkillGap.user_id == user_id)
            .order_by(SkillGap.created_at.desc())
            .all()
        )

    # --- roadmaps ---

    def add_roadmap(self, roadmap: LearningRoadmap) -> LearningRoadmap:
        self.db.add(roadmap)
        self.db.flush()
        return roadmap

    def roadmaps_for_user(self, user_id: uuid.UUID) -> list[LearningRoadmap]:
        return (
            self.db.query(LearningRoadmap)
            .filter(LearningRoadmap.user_id == user_id)
            .order_by(LearningRoadmap.created_at.desc())
            .all()
        )

    def get_roadmap(
        self, roadmap_id: uuid.UUID, user_id: uuid.UUID
    ) -> LearningRoadmap | None:
        return (
            self.db.query(LearningRoadmap)
            .filter(
                LearningRoadmap.id == roadmap_id, LearningRoadmap.user_id == user_id
            )
            .first()
        )
