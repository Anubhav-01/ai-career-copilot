"""Initial schema: users, profiles, resumes, jobs, embeddings (pgvector),
matches, skill gaps, roadmaps, interviews, applications, audit logs.

Revision ID: 0001
Revises:
Create Date: 2025-01-01

The initial revision creates the full schema from the SQLAlchemy metadata
(single source of truth) plus PostgreSQL-specific artifacts: the `vector`
extension and an HNSW cosine index on embeddings. Subsequent schema
changes must be expressed as explicit alembic operations.
"""
from alembic import op

from app.db.base import Base
from app.models import *  # noqa: F401,F403 - register all models

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    Base.metadata.create_all(bind=bind)
    if bind.dialect.name == "postgresql":
        op.execute(
            "CREATE INDEX IF NOT EXISTS ix_embeddings_embedding_hnsw "
            "ON embeddings USING hnsw (embedding vector_cosine_ops)"
        )


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
