"""RAG indexing: chunk -> embed -> store in pgvector with metadata."""
import uuid

from sqlalchemy.orm import Session

from app.ai.embeddings.base import EmbeddingProvider
from app.ai.rag.chunking import Chunk, chunk_job, chunk_resume
from app.core.logging import get_logger, log_event
from app.models.embedding import DocumentEmbedding

logger = get_logger(__name__)


def index_document(
    db: Session,
    embedder: EmbeddingProvider,
    user_id: uuid.UUID,
    document_id: uuid.UUID,
    document_type: str,
    text: str,
) -> int:
    """(Re)index a document. Returns the number of chunks stored."""
    chunks: list[Chunk] = (
        chunk_resume(text) if document_type == "resume" else chunk_job(text)
    )
    if not chunks:
        return 0

    # Idempotent re-index: replace previous chunks for this document.
    db.query(DocumentEmbedding).filter(
        DocumentEmbedding.document_id == document_id,
        DocumentEmbedding.document_type == document_type,
    ).delete(synchronize_session=False)

    vectors = embedder.embed([c.content for c in chunks])
    for chunk, vector in zip(chunks, vectors, strict=True):
        db.add(DocumentEmbedding(
            user_id=user_id,
            document_id=document_id,
            document_type=document_type,
            chunk_index=chunk.index,
            content=chunk.content,
            embedding=vector,
            meta=chunk.meta,
        ))
    db.flush()
    log_event(logger, "rag_indexed", ai_operation="index",
              document_type=document_type, chunks=len(chunks))
    return len(chunks)
