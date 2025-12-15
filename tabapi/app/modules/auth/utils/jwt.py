"""
JWT token utilities for authentication.
"""

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

import jwt

from tabapi.app.modules.auth.config import auth_settings


def create_access_token(
    user_id: int,
    expires_delta: timedelta | None = None,
) -> str:
    """
    Create a JWT access token.

    Args:
        user_id: The user ID to encode in the token.
        expires_delta: Optional custom expiration time.

    Returns:
        The encoded JWT token string.
    """
    now = datetime.now(timezone.utc)
    expire = now + (
        expires_delta
        or timedelta(minutes=auth_settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    payload = {
        "sub": str(user_id),
        "exp": expire,
        "iat": now,
        "jti": str(uuid4()),
        "type": "access",
    }
    return jwt.encode(
        payload,
        auth_settings.JWT_SECRET,
        algorithm=auth_settings.JWT_ALGORITHM,
    )


def create_refresh_token(
    user_id: int,
    expires_delta: timedelta | None = None,
) -> str:
    """
    Create a JWT refresh token.

    Args:
        user_id: The user ID to encode in the token.
        expires_delta: Optional custom expiration time.

    Returns:
        The encoded JWT refresh token string.
    """
    now = datetime.now(timezone.utc)
    expire = now + (
        expires_delta or timedelta(days=auth_settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    )

    payload = {
        "sub": str(user_id),
        "exp": expire,
        "iat": now,
        "jti": str(uuid4()),
        "type": "refresh",
    }
    return jwt.encode(
        payload,
        auth_settings.JWT_SECRET,
        algorithm=auth_settings.JWT_ALGORITHM,
    )


def create_change_token(user_id: int, purpose: str) -> str:
    """
    Create a short-lived token for sensitive operations (e.g., email change).

    Args:
        user_id: The user ID to encode in the token.
        purpose: The purpose of the token (e.g., 'email_change').

    Returns:
        The encoded JWT change token string.
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=auth_settings.CHANGE_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": str(user_id),
        "exp": expire,
        "iat": now,
        "jti": str(uuid4()),
        "type": "change",
        "purpose": purpose,
    }
    return jwt.encode(
        payload,
        auth_settings.JWT_SECRET,
        algorithm=auth_settings.JWT_ALGORITHM,
    )


def decode_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT token.

    Args:
        token: The JWT token string to decode.

    Returns:
        The decoded token payload.

    Raises:
        jwt.ExpiredSignatureError: If the token has expired.
        jwt.InvalidTokenError: If the token is invalid.
    """
    return jwt.decode(
        token,
        auth_settings.JWT_SECRET,
        algorithms=[auth_settings.JWT_ALGORITHM],
    )
