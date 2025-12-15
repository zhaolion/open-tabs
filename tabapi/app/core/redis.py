"""
Redis connection management for TabAPI.
"""

from collections.abc import AsyncIterator

import redis.asyncio as redis

from tabapi.app.core.config import settings

# Global Redis client instance
_redis_client: redis.Redis | None = None


async def get_redis_client() -> redis.Redis:
    """
    Get or create a Redis client instance.

    Returns:
        redis.Redis: The Redis client instance.
    """
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
        )
    return _redis_client


async def close_redis_client() -> None:
    """
    Close the Redis client connection.
    """
    global _redis_client
    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None


async def get_redis() -> AsyncIterator[redis.Redis]:
    """
    Dependency for getting Redis client in FastAPI routes.

    Yields:
        redis.Redis: The Redis client instance.
    """
    client = await get_redis_client()
    yield client
