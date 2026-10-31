"""Redis Cache Layer for Product Catalog.

Provides cache-aside caching for catalog listings and product details with
automatic fallback to direct PostgreSQL if Redis is unreachable.
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any, Optional

logger = logging.getLogger("product-service.cache")

_redis_client = None
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
CACHE_TTL_SECONDS = int(os.getenv("CATALOG_CACHE_TTL", "60"))


def get_redis_client():
    """Lazily initialize Redis connection with socket timeout."""
    global _redis_client
    if _redis_client is not None:
        return _redis_client

    if not REDIS_URL:
        return None

    try:
        import redis
        _redis_client = redis.Redis.from_url(
            REDIS_URL,
            decode_responses=True,
            socket_timeout=1.0,
            socket_connect_timeout=1.0,
        )
        # Quick ping to verify connectivity
        _redis_client.ping()
        logger.info("Connected to Redis cache at %s", REDIS_URL)
        return _redis_client
    except Exception as exc:
        logger.warning("Redis unavailable (%s); operating in database-only mode", exc)
        _redis_client = None
        return None


def get_cached_catalog(cache_key: str) -> Optional[dict]:
    """Retrieve catalog result from Redis cache if available."""
    client = get_redis_client()
    if not client:
        return None
    try:
        data = client.get(cache_key)
        if data:
            return json.loads(data)
    except Exception as exc:
        logger.warning("Redis GET error for key '%s': %s", cache_key, exc)
    return None


def set_cached_catalog(cache_key: str, payload: dict, ttl: int = CACHE_TTL_SECONDS) -> None:
    """Store catalog result in Redis cache with TTL."""
    client = get_redis_client()
    if not client:
        return
    try:
        client.setex(cache_key, ttl, json.dumps(payload))
    except Exception as exc:
        logger.warning("Redis SET error for key '%s': %s", cache_key, exc)


def invalidate_catalog_cache() -> None:
    """Invalidate all catalog cache keys upon product or stock mutations."""
    client = get_redis_client()
    if not client:
        return
    try:
        keys = client.keys("catalog:*")
        if keys:
            client.delete(*keys)
            logger.info("Invalidated %d catalog cache keys", len(keys))
    except Exception as exc:
        logger.warning("Redis cache invalidation error: %s", exc)
