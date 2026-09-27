from app.ai.embeddings.base import EmbeddingProvider
from app.ai.embeddings.hashing import HashingEmbeddingProvider
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_provider: EmbeddingProvider | None = None


def get_embedding_provider() -> EmbeddingProvider:
    global _provider
    if _provider is None:
        settings = get_settings()
        if settings.embedding_provider == "sentence-transformer":
            try:
                from app.ai.embeddings.sentence_transformer import (
                    SentenceTransformerProvider,
                )

                _provider = SentenceTransformerProvider()
            except ImportError:
                logger.warning(
                    "sentence-transformers not installed; falling back to"
                    " lexical hashing embedder (install requirements-ml.txt"
                    " for semantic embeddings)"
                )
                _provider = HashingEmbeddingProvider(settings.embedding_dimension)
        else:
            _provider = HashingEmbeddingProvider(settings.embedding_dimension)
    return _provider


def reset_embedding_provider() -> None:
    """Test helper."""
    global _provider
    _provider = None
