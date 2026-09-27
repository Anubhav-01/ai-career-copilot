"""Cache abstraction: Redis when configured, in-memory fallback otherwise.

Used for dashboard aggregates and idempotent AI results (keyed by content
hash). Sensitive raw resume text is never cached; only derived, per-user
results keyed by user id.
"""
import json
import threading
import time
from typing import Any, Protocol

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class Cache(Protocol):
    def get(self, key: str) -> Any | None: ...
    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None: ...
    def delete(self, key: str) -> None: ...
    def delete_prefix(self, prefix: str) -> None: ...


class InMemoryCache:
    """Thread-safe TTL cache used in tests and when Redis is unavailable."""

    def __init__(self) -> None:
        self._data: dict[str, tuple[float, Any]] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Any | None:
        with self._lock:
            item = self._data.get(key)
            if item is None:
                return None
            expires_at, value = item
            if expires_at and expires_at < time.time():
                del self._data[key]
                return None
            return value

    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        expires_at = time.time() + ttl_seconds if ttl_seconds else 0.0
        with self._lock:
            self._data[key] = (expires_at, value)

    def delete(self, key: str) -> None:
        with self._lock:
            self._data.pop(key, None)

    def delete_prefix(self, prefix: str) -> None:
        with self._lock:
            for key in [k for k in self._data if k.startswith(prefix)]:
                del self._data[key]


class RedisCache:
    def __init__(self, url: str) -> None:
        import redis

        self._client = redis.Redis.from_url(url, decode_responses=True)

    def get(self, key: str) -> Any | None:
        raw = self._client.get(key)
        return json.loads(raw) if raw is not None else None

    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        self._client.set(key, json.dumps(value, default=str), ex=ttl_seconds)

    def delete(self, key: str) -> None:
        self._client.delete(key)

    def delete_prefix(self, prefix: str) -> None:
        for key in self._client.scan_iter(f"{prefix}*"):
            self._client.delete(key)


_cache: Cache | None = None


def get_cache() -> Cache:
    global _cache
    if _cache is None:
        settings = get_settings()
        if settings.redis_url:
            try:
                candidate = RedisCache(settings.redis_url)
                candidate.set("__healthcheck__", "ok", ttl_seconds=5)
                _cache = candidate
                logger.info("Using Redis cache")
            except Exception:
                logger.warning("Redis unavailable, using in-memory cache")
                _cache = InMemoryCache()
        else:
            _cache = InMemoryCache()
    return _cache


def reset_cache() -> None:
    """Test helper."""
    global _cache
    _cache = None
