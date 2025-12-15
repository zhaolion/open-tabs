"""
Authentication module dependencies for FastAPI routes.
"""

from typing import Annotated

import jwt
from fastapi import Depends, Header, Request
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from tabapi.app.db.deps import get_db as get_session
from tabapi.app.core.redis import get_redis
from tabapi.app.modules.auth.enums import UserStatus
from tabapi.app.modules.auth.exceptions import (
    InvalidSignatureException,
    NonceAlreadyUsedException,
    TimestampExpiredException,
    TokenExpiredException,
    TokenInvalidException,
    UserNotFoundException,
    UserSuspendedException,
)
from tabapi.app.modules.auth.models import User
from tabapi.app.modules.auth.schemas import SecureRequestMixin
from tabapi.app.modules.auth.service import AuthService
from tabapi.app.modules.auth.utils.jwt import decode_token
from tabapi.app.modules.auth.utils.nonce import validate_and_consume_nonce
from tabapi.app.modules.auth.utils.signature import (
    validate_auth_timestamp,
    verify_signature,
)


async def get_auth_service(
    db: Annotated[AsyncSession, Depends(get_session)],
) -> AuthService:
    """Get AuthService instance with database session."""
    return AuthService(db)


def get_token_from_header(
    authorization: Annotated[str | None, Header()] = None,
) -> str:
    """
    Extract JWT token from Authorization header.

    Args:
        authorization: The Authorization header value.

    Returns:
        The JWT token string.

    Raises:
        TokenInvalidException: If the header is missing or malformed.
    """
    if not authorization:
        raise TokenInvalidException()

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise TokenInvalidException()

    return parts[1]


async def get_current_user(
    token: Annotated[str, Depends(get_token_from_header)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> User:
    """
    Get the current authenticated user from JWT token.

    Args:
        token: The JWT access token.
        auth_service: The authentication service.

    Returns:
        The authenticated User object.

    Raises:
        TokenExpiredException: If the token has expired.
        TokenInvalidException: If the token is invalid.
        UserNotFoundException: If the user doesn't exist.
    """
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise TokenInvalidException()

        user_id = int(payload.get("sub", 0))
        if not user_id:
            raise TokenInvalidException()

    except jwt.ExpiredSignatureError:
        raise TokenExpiredException()
    except (jwt.InvalidTokenError, ValueError):
        raise TokenInvalidException()

    user = await auth_service.get_user_by_id(user_id)
    if not user:
        raise UserNotFoundException()

    return user


async def get_current_active_user(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Get the current active user (not suspended or deleted).

    Args:
        user: The authenticated user.

    Returns:
        The active User object.

    Raises:
        UserSuspendedException: If the user is suspended.
        UserNotFoundException: If the user is deleted.
    """
    if user.status == UserStatus.SUSPENDED.value:
        raise UserSuspendedException()
    if user.status == UserStatus.DELETED.value:
        raise UserNotFoundException()

    return user


def get_client_ip(request: Request) -> str | None:
    """
    Get client IP address from request.

    Args:
        request: The FastAPI request object.

    Returns:
        The client IP address or None.
    """
    # Check X-Forwarded-For header for proxied requests
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP in the list
        return forwarded_for.split(",")[0].strip()

    # Fall back to direct client IP
    if request.client:
        return request.client.host

    return None


def get_user_agent(request: Request) -> str | None:
    """
    Get User-Agent from request headers.

    Args:
        request: The FastAPI request object.

    Returns:
        The User-Agent string or None.
    """
    return request.headers.get("User-Agent")


class SecureRequestValidator:
    """
    Dependency for validating secure request fields (nonce, timestamp, signature).
    Used for anti-replay attack protection.
    """

    def __init__(self, purpose_field: str = "purpose"):
        """
        Initialize the validator.

        Args:
            purpose_field: The field name that contains the purpose value.
        """
        self.purpose_field = purpose_field

    async def __call__(
        self,
        request_data: SecureRequestMixin,
        redis: Annotated[Redis, Depends(get_redis)],
    ) -> SecureRequestMixin:
        """
        Validate secure request fields.

        Args:
            request_data: The request data containing security fields.
            redis: Redis client for nonce validation.

        Returns:
            The validated request data.

        Raises:
            TimestampExpiredException: If the timestamp is too old.
            NonceAlreadyUsedException: If the nonce has been used.
            InvalidSignatureException: If the signature is invalid.
        """
        # Get email and purpose from request data
        email = getattr(request_data, "email", "")
        purpose = getattr(request_data, self.purpose_field, "")

        # Validate timestamp
        if not validate_auth_timestamp(request_data.auth_at):
            raise TimestampExpiredException()

        # Validate and consume nonce atomically
        nonce_valid = await validate_and_consume_nonce(redis, request_data.nonce)
        if not nonce_valid:
            raise NonceAlreadyUsedException()

        # Verify signature
        if not verify_signature(
            email=email,
            nonce=request_data.nonce,
            auth_at=request_data.auth_at,
            purpose=purpose,
            signature=request_data.signature,
        ):
            raise InvalidSignatureException()

        return request_data


# Pre-configured validators for common purposes
validate_verification_request = SecureRequestValidator(purpose_field="purpose")
validate_registration_request = SecureRequestValidator(purpose_field="purpose")
validate_login_request = SecureRequestValidator(purpose_field="purpose")
validate_email_binding_request = SecureRequestValidator(purpose_field="purpose")
validate_email_change_request = SecureRequestValidator(purpose_field="purpose")


async def validate_secure_request(
    request_data: SecureRequestMixin,
    redis: Annotated[Redis, Depends(get_redis)],
    email: str,
    purpose: str,
) -> None:
    """
    Standalone function to validate secure request fields.

    Args:
        request_data: The request data containing security fields.
        redis: Redis client for nonce validation.
        email: Email address to include in signature verification.
        purpose: Purpose to include in signature verification.

    Raises:
        TimestampExpiredException: If the timestamp is too old.
        NonceAlreadyUsedException: If the nonce has been used.
        InvalidSignatureException: If the signature is invalid.
    """
    # Validate timestamp
    if not validate_auth_timestamp(request_data.auth_at):
        raise TimestampExpiredException()

    # Validate and consume nonce atomically
    nonce_valid = await validate_and_consume_nonce(redis, request_data.nonce)
    if not nonce_valid:
        raise NonceAlreadyUsedException()

    # Verify signature
    if not verify_signature(
        email=email,
        nonce=request_data.nonce,
        auth_at=request_data.auth_at,
        purpose=purpose,
        signature=request_data.signature,
    ):
        raise InvalidSignatureException()
