"""
Nonce storage utilities for anti-replay attack protection.
Uses Redis to store and check used nonces.
"""

from redis.asyncio import Redis

from tabapi.app.modules.auth.config import auth_settings

# Redis key prefix for nonces
NONCE_KEY_PREFIX = "auth:nonce:"


async def is_nonce_used(redis: Redis, nonce: str) -> bool:
    """
    Check if a nonce has already been used.

    Args:
        redis: The Redis client instance.
        nonce: The nonce to check.

    Returns:
        True if the nonce has been used, False otherwise.
    """
    key = f"{NONCE_KEY_PREFIX}{nonce}"
    return await redis.exists(key) > 0


async def mark_nonce_used(redis: Redis, nonce: str) -> None:
    """
    Mark a nonce as used by storing it in Redis with TTL.

    Args:
        redis: The Redis client instance.
        nonce: The nonce to mark as used.
    """
    key = f"{NONCE_KEY_PREFIX}{nonce}"
    await redis.set(
        key,
        "1",
        ex=auth_settings.NONCE_TTL_SECONDS,
    )


async def validate_and_consume_nonce(redis: Redis, nonce: str) -> bool:
    """
    Atomically check if a nonce is unused and mark it as used.

    Uses Redis SETNX to ensure atomicity.

    Args:
        redis: The Redis client instance.
        nonce: The nonce to validate and consume.

    Returns:
        True if the nonce was unused and is now consumed, False if already used.
    """
    key = f"{NONCE_KEY_PREFIX}{nonce}"
    # SETNX returns True if key was set (nonce was unused)
    result = await redis.setnx(key, "1")
    if result:
        # Set expiration time
        await redis.expire(key, auth_settings.NONCE_TTL_SECONDS)
    return bool(result)
