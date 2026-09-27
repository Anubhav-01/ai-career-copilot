import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import GUID, Base, EmbeddingVector, utcnow, uuid_pk

EMBEDDING_DIM = 384


class DocumentEmbedding(Base):
    """One embedded chunk of a user document (resume or job description).

    Metadata is stored alongside every vector so retrieval can filter by
    user, document and type before ranking by cosine distance.
    """

    __tablename__ = "embeddings"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    document_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False)
    document_type: Mapped[str] = mapped_column(String(20), nullable=False)  # resume | job
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(
        EmbeddingVector(EMBEDDING_DIM), nullable=False
    )
    meta: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    __table_args__ = (
        Index("ix_embeddings_doc", "document_id", "document_type"),
        Index("ix_embeddings_user_type", "user_id", "document_type"),
    )
