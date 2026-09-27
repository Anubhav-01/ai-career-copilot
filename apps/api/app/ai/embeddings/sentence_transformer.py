"""Sentence-transformers embedding provider (all-MiniLM-L6-v2 by default).

The model is loaded once per process and reused (embedding reuse & cost
control). Requires `requirements-ml.txt` extras.
"""
from app.ai.embeddings.base import EmbeddingProvider
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class SentenceTransformerProvider(EmbeddingProvider):
    name = "sentence-transformer"

    def __init__(self, model_name: str | None = None):
        from sentence_transformers import SentenceTransformer

        settings = get_settings()
        self._model = SentenceTransformer(model_name or settings.embedding_model)
        self.dimension = int(self._model.get_sentence_embedding_dimension())
        logger.info("Loaded embedding model (dim=%s)", self.dimension)

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors = self._model.encode(
            texts, normalize_embeddings=True, show_progress_bar=False
        )
        return [v.tolist() for v in vectors]
