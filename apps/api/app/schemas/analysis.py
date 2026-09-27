"""Resume analysis / ATS-style analysis schemas."""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ScoreComponent(BaseModel):
    key: str
    label: str
    score: float = Field(ge=0, le=100)
    weight: float = Field(ge=0, le=1)
    explanation: str


class ATSFinding(BaseModel):
    severity: str  # info | warning | critical
    category: str
    problem: str
    recommendation: str


class ATSResult(BaseModel):
    """ATS-style analysis. This is a heuristic simulation for guidance -
    it does not claim to reproduce any proprietary ATS."""

    score: float = Field(ge=0, le=100)
    findings: list[ATSFinding] = Field(default_factory=list)
    action_verb_count: int = 0
    quantified_bullet_ratio: float = 0.0
    detected_sections: list[str] = Field(default_factory=list)
    missing_sections: list[str] = Field(default_factory=list)
    keyword_stuffing_detected: bool = False


class Recommendation(BaseModel):
    priority: str  # high | medium | low
    category: str
    problem: str
    recommendation: str


class ResumeAnalysisOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    resume_id: uuid.UUID
    overall_score: float
    scores: dict
    ats: dict
    recommendations: list
    explanation: str | None = None
    weights: dict
    created_at: datetime
