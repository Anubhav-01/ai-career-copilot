"""Application configuration loaded from environment variables."""
from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ScoreWeights(BaseSettings):
    """Configurable weights for the resume score. Must sum to 1.0."""

    ats: float = 0.25
    skills: float = 0.20
    experience: float = 0.20
    projects: float = 0.15
    keyword_coverage: float = 0.10
    structure: float = 0.10

    model_config = SettingsConfigDict(env_prefix="RESUME_SCORE_WEIGHT_")


class MatchWeights(BaseSettings):
    """Configurable weights for the hybrid job-match score. Must sum to 1.0."""

    semantic: float = 0.40
    required_skills: float = 0.25
    preferred_skills: float = 0.15
    experience: float = 0.10
    education: float = 0.05
    keywords: float = 0.05

    model_config = SettingsConfigDict(env_prefix="MATCH_WEIGHT_")


class Settings(BaseSettings):
    app_name: str = "AI Career Copilot"
    environment: str = Field(default="development", alias="ENVIRONMENT")
    debug: bool = False

    # Database
    database_url: str = Field(
        default="sqlite:///./career_copilot.db", alias="DATABASE_URL"
    )

    # Auth
    jwt_secret: str = Field(default="dev-only-secret-change-me", alias="JWT_SECRET")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(
        default=30, alias="ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    refresh_token_expire_days: int = Field(default=7, alias="REFRESH_TOKEN_EXPIRE_DAYS")

    # LLM
    llm_provider: str = Field(default="mock", alias="LLM_PROVIDER")
    llm_api_key: str = Field(default="", alias="LLM_API_KEY")
    llm_model: str = Field(default="gpt-4o-mini", alias="LLM_MODEL")
    llm_timeout_seconds: float = Field(default=45.0, alias="LLM_TIMEOUT_SECONDS")
    llm_max_retries: int = Field(default=2, alias="LLM_MAX_RETRIES")

    # Embeddings
    embedding_provider: str = Field(
        default="sentence-transformer", alias="EMBEDDING_PROVIDER"
    )
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2", alias="EMBEDDING_MODEL"
    )
    embedding_dimension: int = Field(default=384, alias="EMBEDDING_DIMENSION")

    # Cache
    redis_url: str = Field(default="", alias="REDIS_URL")
    cache_ttl_seconds: int = 300

    # API
    cors_origins: str = Field(default="http://localhost:3000", alias="CORS_ORIGINS")
    rate_limit_per_minute: int = Field(default=120, alias="RATE_LIMIT_PER_MINUTE")
    max_upload_size_mb: int = Field(default=5, alias="MAX_UPLOAD_SIZE_MB")
    upload_dir: str = "uploads"

    # Scoring (documented in docs/ai.md)
    resume_score_weights: ScoreWeights = ScoreWeights()
    match_weights: MatchWeights = MatchWeights()

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    @field_validator("llm_provider")
    @classmethod
    def _valid_llm_provider(cls, v: str) -> str:
        allowed = {"mock", "openai"}
        if v not in allowed:
            raise ValueError(f"LLM_PROVIDER must be one of {allowed}")
        return v

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()
