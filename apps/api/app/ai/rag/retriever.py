"""Semantic retrieval over stored embeddings.

On PostgreSQL the ranking runs in-database using pgvector's cosine
distance operator (`<=>`), filtered by user/document metadata first.
On other dialects (unit tests) it falls back to in-Python cosine.
"""
import uuid
from dataclasses import dataclass

import numpy as np
from sqlalchemy import text as sql_text
from sqlalchemy.orm import Session

from app.ai.embeddings.base import EmbeddingProvider
from app.models.embedding import DocumentEmbedding


@dataclass
class RetrievedChunk:
    content: str
    similarity: float  # cosine similarity in [-1, 1]
    document_id: uuid.UUID
    document_type: str
    chunk_index: int
    meta: dict | None


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    denom = float(np.linalg.norm(a) * np.linalg.norm(b)) or 1.0
    return float(np.dot(a, b)) / denom


class Retriever:
    def __init__(self, db: Session, embedder: EmbeddingProvider):
        self.db = db
        self.embedder = embedder

    def search(
        self,
        user_id: uuid.UUID,
        query: str,
        top_k: int = 5,
        document_type: str | None = None,
        document_id: uuid.UUID | None = None,
    ) -> list[RetrievedChunk]:
        query_vector = self.embedder.embed_one(query)
        if self.db.get_bind().dialect.name == "postgresql":
            return self._search_pgvector(
                user_id, query_vector, top_k, document_type, document_id
            )
        return self._search_python(
            user_id, query_vector, top_k, document_type, document_id
        )

    def _search_pgvector(
        self, user_id, query_vector, top_k, document_type, document_id
    ) -> list[RetrievedChunk]:
        filters = ["user_id = :user_id"]
        params: dict = {
            "user_id": str(user_id),
            "vec": str(query_vector),
            "top_k": top_k,
        }
        if document_type:
            filters.append("document_type = :document_type")
            params["document_type"] = document_type
        if document_id:
            filters.append("document_id = :document_id")
            params["document_id"] = str(document_id)

        rows = self.db.execute(sql_text(
            f"""
            SELECT content, document_id, document_type, chunk_index, meta,
                   1 - (embedding <=> CAST(:vec AS vector)) AS similarity
            FROM embeddings
            WHERE {' AND '.join(filters)}
            ORDER BY embedding <=> CAST(:vec AS vector)
            LIMIT :top_k
            """
        ), params).fetchall()

        return [
            RetrievedChunk(
                content=row.content,
                similarity=float(row.similarity),
                document_id=uuid.UUID(str(row.document_id)),
                document_type=row.document_type,
                chunk_index=row.chunk_index,
                meta=row.meta,
            )
            for row in rows
        ]

    def _search_python(
        self, user_id, query_vector, top_k, document_type, document_id
    ) -> list[RetrievedChunk]:
        query_np = np.array(query_vector)
        stmt = self.db.query(DocumentEmbedding).filter(
            DocumentEmbedding.user_id == user_id
        )
        if document_type:
            stmt = stmt.filter(DocumentEmbedding.document_type == document_type)
        if document_id:
            stmt = stmt.filter(DocumentEmbedding.document_id == document_id)

        scored = [
            RetrievedChunk(
                content=row.content,
                similarity=_cosine(query_np, np.array(row.embedding)),
                document_id=row.document_id,
                document_type=row.document_type,
                chunk_index=row.chunk_index,
                meta=row.meta,
            )
            for row in stmt.all()
        ]
        scored.sort(key=lambda c: c.similarity, reverse=True)
        return scored[:top_k]

    def document_similarity(
        self,
        user_id: uuid.UUID,
        source_document_id: uuid.UUID,
        target_document_id: uuid.UUID,
        top_k_per_chunk: int = 3,
    ) -> float:
        """Average of each source chunk's best matches in the target document
        (used for resume <-> job semantic similarity)."""
        source_chunks = (
            self.db.query(DocumentEmbedding)
            .filter(
                DocumentEmbedding.user_id == user_id,
                DocumentEmbedding.document_id == source_document_id,
            )
            .all()
        )
        if not source_chunks:
            return 0.0
        best_scores: list[float] = []
        for chunk in source_chunks:
            target_np = self._top_similarities(
                user_id, chunk.embedding, target_document_id, top_k_per_chunk
            )
            if target_np:
                best_scores.append(max(target_np))
        return float(np.mean(best_scores)) if best_scores else 0.0

    def _top_similarities(
        self, user_id, vector, document_id, top_k
    ) -> list[float]:
        if self.db.get_bind().dialect.name == "postgresql":
            rows = self.db.execute(sql_text(
                """
                SELECT 1 - (embedding <=> CAST(:vec AS vector)) AS similarity
                FROM embeddings
                WHERE user_id = :user_id AND document_id = :document_id
                ORDER BY embedding <=> CAST(:vec AS vector)
                LIMIT :top_k
                """
            ), {
                "vec": str(list(vector)), "user_id": str(user_id),
                "document_id": str(document_id), "top_k": top_k,
            }).fetchall()
            return [float(r.similarity) for r in rows]

        vector_np = np.array(vector)
        rows = self.db.query(DocumentEmbedding).filter(
            DocumentEmbedding.user_id == user_id,
            DocumentEmbedding.document_id == document_id,
        ).all()
        sims = sorted(
            (_cosine(vector_np, np.array(r.embedding)) for r in rows), reverse=True
        )
        return sims[:top_k]
