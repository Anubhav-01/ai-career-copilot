"""Import all models so `Base.metadata` is complete for Alembic and tests."""
from app.models.application import Application
from app.models.audit import AuditLog
from app.models.embedding import DocumentEmbedding
from app.models.interview import Interview, InterviewAnswer, InterviewQuestion
from app.models.job import Job, JobSkill
from app.models.match import JobMatch, LearningRoadmap, SkillGap
from app.models.resume import Resume, ResumeAnalysis, ResumeSection, ResumeSkill
from app.models.user import Profile, RefreshToken, User

__all__ = [
    "Application",
    "AuditLog",
    "DocumentEmbedding",
    "Interview",
    "InterviewAnswer",
    "InterviewQuestion",
    "Job",
    "JobSkill",
    "JobMatch",
    "LearningRoadmap",
    "SkillGap",
    "Resume",
    "ResumeAnalysis",
    "ResumeSection",
    "ResumeSkill",
    "Profile",
    "RefreshToken",
    "User",
]
