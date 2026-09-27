"""Simple sliding-window rate limiter (per client IP + path group).

In-process implementation suitable for a single instance; swap the store
for Redis (INCR + EXPIRE) when running multiple replicas.
"""
import threading
import time

from app.core.errors import RateLimitExceededError


class SlidingWindowRateLimiter:
    def __init__(self, max_requests: int, window_seconds: int = 60) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def check(self, key: str) -> None:
        now = time.time()
        cutoff = now - self.window_seconds
        with self._lock:
            hits = [t for t in self._hits.get(key, []) if t > cutoff]
            if len(hits) >= self.max_requests:
                raise RateLimitExceededError()
            hits.append(now)
            self._hits[key] = hits

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()
