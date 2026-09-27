from pydantic import BaseModel, Field


class ScorePoint(BaseModel):
    date: str
    score: float


class SkillCoverageItem(BaseModel):
    skill: str
    count: int


class FunnelStage(BaseModel):
    status: str
    count: int


class MatchDistributionBucket(BaseModel):
    bucket: str  # e.g. "80-100"
    count: int


class InterviewPerformancePoint(BaseModel):
    date: str
    score: float


class DashboardOut(BaseModel):
    resume_count: int = 0
    latest_resume_score: float | None = None
    profile_completeness: float = 0
    top_skills: list[SkillCoverageItem] = Field(default_factory=list)
    skill_gap_count: int = 0
    top_gaps: list[str] = Field(default_factory=list)
    target_roles: list[str] = Field(default_factory=list)
    job_count: int = 0
    match_count: int = 0
    best_match_score: float | None = None
    application_count: int = 0
    score_history: list[ScorePoint] = Field(default_factory=list)
    match_distribution: list[MatchDistributionBucket] = Field(default_factory=list)
    application_funnel: list[FunnelStage] = Field(default_factory=list)
    interview_performance: list[InterviewPerformancePoint] = Field(default_factory=list)


class AdminStats(BaseModel):
    total_users: int = 0
    total_resumes: int = 0
    total_jobs: int = 0
    total_matches: int = 0
    total_interviews: int = 0
    ai_requests: int = 0
    ai_errors: int = 0
    avg_resume_processing_seconds: float | None = None
