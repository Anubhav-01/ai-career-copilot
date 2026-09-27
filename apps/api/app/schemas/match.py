import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MatchRequest(BaseModel):
    resume_id: uuid.UUID


class SkillEvidence(BaseModel):
    skill: str
    evidence: str
    section: str | None = None


class MatchComponents(BaseModel):
    semantic: float = Field(ge=0, le=100)
    required_skills: float = Field(ge=0, le=100)
    preferred_skills: float = Field(ge=0, le=100)
    experience: float = Field(ge=0, le=100)
    education: float = Field(ge=0, le=100)
    keywords: float = Field(ge=0, le=100)


class MatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    resume_id: uuid.UUID
    job_id: uuid.UUID
    overall_score: float
    components: dict
    strong_matches: list
    partial_matches: list
    missing_skills: list
    evidence: list
    explanation: str | None = None
    weights: dict
    created_at: datetime


class SkillGapItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    skill: str
    normalized: str
    priority: str
    reason: str | None = None
    job_id: uuid.UUID | None = None
    created_at: datetime


class RoadmapStage(BaseModel):
    period: str  # e.g. "Week 1"
    focus: str
    practice_task: str


class LearningRoadmapSchema(BaseModel):
    """Validated structure for LLM roadmap output. Course URLs are
    deliberately excluded to avoid fabricated links."""

    skill: str
    priority: str = "important"
    prerequisites: list[str] = Field(default_factory=list)
    stages: list[RoadmapStage] = Field(default_factory=list)
    project_idea: str = ""
    estimated_weeks: int = Field(default=4, ge=1, le=52)


class LearningRoadmapOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    skill: str
    priority: str
    estimated_weeks: int
    content: LearningRoadmapSchema
    created_at: datetime
