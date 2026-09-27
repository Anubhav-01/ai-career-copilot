"""Embedding provider abstraction."""
from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    name: str = "base"
    dimension: int = 384

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts into unit-normalized vectors."""
        raise NotImplementedError

    def embed_one(self, text: str) -> list[float]:
        return self.embed([text])[0]
