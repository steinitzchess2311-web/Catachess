"""
Simple in-memory rate limiter for API endpoints.
"""

import os
import time
from collections import deque


class RateLimiter:
    def __init__(self) -> None:
        self._buckets: dict[str, deque[float]] = {}

    def allow(self, key: str, limit: int, window_seconds: int) -> bool:
        if os.getenv("DISABLE_RATE_LIMIT") == "1":
            print(f"DEBUG: RateLimiter disabled by env")
            return True
        if limit <= 0:
            return True
        now = time.monotonic()
        bucket = self._buckets.get(key)
        if bucket is None:
            bucket = deque()
            self._buckets[key] = bucket

        cutoff = now - window_seconds
        while bucket and bucket[0] <= cutoff:
            bucket.popleft()

        print(f"DEBUG: RateLimiter check key={key} limit={limit} current={len(bucket)}")

        if len(bucket) >= limit:
            print(f"DEBUG: RateLimiter REJECTED")
            return False

        bucket.append(now)
        print(f"DEBUG: RateLimiter ALLOWED")
        return True

    def reset(self, key: str | None = None) -> None:
        if key is None:
            self._buckets.clear()
        else:
            self._buckets.pop(key, None)
