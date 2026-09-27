"""Dependency-free fallback embedder (feature hashing of word n-grams).

This is NOT a semantic model - it only captures lexical overlap. It exists
so the application and test suite run in environments without the ML
extras installed. Production must use SentenceTransformerProvider; the
active provider is reported by /health so the difference is transparent.
"""
import hashlib
import math
import re

from app.ai.embeddings.base import EmbeddingProvider

_TOKEN_RE = re.compile(r"[a-z0-9+#.]+")


class HashingEmbeddingProvider(EmbeddingProvider):
    name = "hashing"

    def __init__(self, dimension: int = 384):
        self.dimension = dimension

    def _tokens(self, text: str) -> list[str]:
        words = _TOKEN_RE.findall(text.lower())
        bigrams = [f"{a}_{b}" for a, b in zip(words, words[1:], strict=False)]
        return words + bigrams

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_single(t) for t in texts]

    def _embed_single(self, text: str) -> list[float]:
        vector = [0.0] * self.dimension
        for token in self._tokens(text):
            digest = hashlib.md5(token.encode()).digest()
            index = int.from_bytes(digest[:4], "little") % self.dimension
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign
        norm = math.sqrt(sum(v * v for v in vector)) or 1.0
        return [v / norm for v in vector]
