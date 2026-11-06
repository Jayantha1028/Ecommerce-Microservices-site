"""Perimeter Sliding-Window Rate Limiter & DDoS Protection Shield.

Implements token bucket / sliding window rate limiting using Redis
with automatic in-memory fallback for high availability.
Protects microservices from brute force authentication attacks and request flooding.
"""
from __future__ import annotations

import collections
import os
import threading
import time
from typing import Optional, Tuple

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/1")

# Route limit policies: (max_requests, window_seconds)
RATE_LIMIT_POLICIES = {
    "auth": (30, 60),       # 30 requests per minute for login/register (brute-force defense)
    "checkout": (45, 60),   # 45 requests per minute for payments/orders
    "default": (180, 60),   # 180 requests per minute for general catalog & storefront
}


class RateLimiter:
    """Thread-safe sliding-window rate limiter with Redis backend and in-memory fallback."""

    def __init__(self, redis_url: str = REDIS_URL):
        self.redis_url = redis_url
        self._redis_client = None
        self._redis_failed = False
        self._in_memory_store: collections.defaultdict = collections.defaultdict(collections.deque)
        self._lock = threading.Lock()

    def _get_redis(self):
        """Lazily initialize Redis connection."""
        if self._redis_failed:
            return None
        if self._redis_client is not None:
            return self._redis_client
        try:
            import redis
            client = redis.Redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_timeout=0.5,
                socket_connect_timeout=0.5,
            )
            client.ping()
            self._redis_client = client
            return client
        except Exception:
            self._redis_failed = True
            return None

    def get_policy(self, path: str) -> Tuple[int, int]:
        """Determine rate limit policy (limit, window_seconds) based on request path."""
        path_lower = path.lower()
        if path_lower.startswith("/auth/login") or path_lower.startswith("/auth/register"):
            return RATE_LIMIT_POLICIES["auth"]
        elif path_lower.startswith("/payments") or path_lower.startswith("/orders"):
            return RATE_LIMIT_POLICIES["checkout"]
        return RATE_LIMIT_POLICIES["default"]

    def is_rate_limited(self, client_ip: str, path: str) -> Tuple[bool, int, int, int]:
        """Check if request exceeds rate limit.

        Returns:
            (is_limited, limit, remaining, reset_seconds)
        """
        # Exclude internal health and telemetry probes from rate limiting
        if path.startswith("/health") or path.startswith("/observability") or path == "/favicon.ico":
            return False, 9999, 9999, 0

        limit, window = self.get_policy(path)
        now = time.time()
        client = self._get_redis()

        if client:
            try:
                key = f"ratelimit:{client_ip}:{path.split('/')[1] if len(path) > 1 else 'root'}"
                pipe = client.pipeline()
                pipe.zremrangebyscore(key, 0, now - window)
                pipe.zadd(key, {str(now): now})
                pipe.zcard(key)
                pipe.expire(key, window)
                _, _, current_count, _ = pipe.execute()

                remaining = max(0, limit - current_count)
                reset_seconds = window
                is_limited = current_count > limit
                return is_limited, limit, remaining, reset_seconds
            except Exception:
                # Redis failure fallback to in-memory sliding window
                pass

        # In-memory sliding window fallback
        with self._lock:
            key = f"{client_ip}:{path.split('/')[1] if len(path) > 1 else 'root'}"
            timestamps = self._in_memory_store[key]
            cutoff = now - window

            while timestamps and timestamps[0] < cutoff:
                timestamps.popleft()

            timestamps.append(now)
            current_count = len(timestamps)
            remaining = max(0, limit - current_count)
            is_limited = current_count > limit
            reset_seconds = int(window - (now - timestamps[0])) if timestamps else window
            return is_limited, limit, remaining, max(1, reset_seconds)


# Global singleton rate limiter
rate_limiter = RateLimiter()
