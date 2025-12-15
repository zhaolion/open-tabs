"""
Authentication module API routes.
"""

from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from tabapi.app.core.redis import get_redis
from tabapi.app.db.deps import get_db
from tabapi.app.modules.auth.config import auth_settings
from tabapi.app.modules.auth.dependencies import (
    get_auth_service,
    get_client_ip,
    get_current_active_user,
    get_user_agent,
    validate_secure_request,
)
from tabapi.app.modules.auth.exceptions import (
    EmailNotFoundException,
    UserNotFoundException,
)
from tabapi.app.modules.auth.models import User
from tabapi.app.modules.auth.schemas import (
    AuthTokenResponse,
    BindEmailRequest,
    BindEmailResponse,
    ChangePasswordRequest,
    ChangePasswordResponse,
    ConfirmEmailChangeRequest,
    ConfirmEmailChangeResponse,
    EmailRegisterRequest,
    PasswordLoginRequest,
    ResetPasswordRequest,
    ResetPasswordResponse,
    SendVerificationCodeRequest,
    SendVerificationCodeResponse,
    UserResponse,
    VerificationCodeLoginRequest,
    VerifyIdentityRequest,
    VerifyIdentityResponse,
)
from tabapi.app.modules.auth.service import AuthService
from tabapi.app.modules.auth.utils.email import get_email_service
from tabapi.app.modules.auth.utils.jwt import create_access_token
from tabapi.app.modules.auth.utils.verification import get_expiry_minutes

# Public routes (no authentication required)
public_router = APIRouter(prefix="/auth/v1", tags=["auth"])

# Protected routes (authentication required)
protected_router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def _create_token_response(user: User) -> AuthTokenResponse:
    """Create authentication token response for a user."""
    access_token = create_access_token(user.id)
    return AuthTokenResponse(
        user=UserResponse(
            uid=user.uid,
            username=user.username,
            email=user.email,
            display_name=user.display_name,
            avatar_url=user.avatar_url,
            status=user.status,
            created_at=user.created_at,
        ),
        access_token=access_token,
        token_type="bearer",
        expires_in=auth_settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


# === Verification Code Routes ===


@public_router.post(
    "/verification-code/send",
    response_model=SendVerificationCodeResponse,
    summary="Send verification code",
    description="Send a verification code to the specified email address.",
)
async def send_verification_code(
    request_data: SendVerificationCodeRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis, Depends(get_redis)],
) -> SendVerificationCodeResponse:
    """Send verification code to email."""
    auth_service = AuthService(db)

    # Validate secure request fields
    await validate_secure_request(
        request_data, redis, request_data.email, request_data.purpose
    )

    # Check business rules based on purpose
    purpose = request_data.purpose
    user = await auth_service.get_user_by_email(request_data.email)

    if purpose == "registration":
        # For registration, email should NOT be registered
        if user is not None:
            from tabapi.app.modules.auth.exceptions import (
                EmailAlreadyRegisteredException,
            )

            raise EmailAlreadyRegisteredException()
    elif purpose in ("login", "password_reset"):
        # For login and password reset, email MUST be registered
        if user is None:
            raise EmailNotFoundException()
    elif purpose == "email_change":
        # For email change, this is the OLD email, user must exist
        if user is None:
            raise UserNotFoundException()

    # Get client info
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)

    # Create verification code
    plain_code, verification_code = await auth_service.create_verification_code(
        email=request_data.email,
        purpose=purpose,
        user_id=user.id if user else None,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    # Send email
    email_service = get_email_service()
    await email_service.send_verification_code(
        email=request_data.email,
        code=plain_code,
        purpose=purpose,
    )

    await db.commit()

    # Calculate expiry and next send time
    expiry_minutes = get_expiry_minutes(purpose)

    return SendVerificationCodeResponse(
        expires_in=expiry_minutes * 60,
        next_send_available_at=datetime.now(timezone.utc) + timedelta(seconds=60),
    )


# === Registration Routes ===


@public_router.post(
    "/register/email",
    response_model=AuthTokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register with email",
    description="Register a new user with email, password, and verification code.",
)
async def register_with_email(
    request_data: EmailRegisterRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis, Depends(get_redis)],
) -> AuthTokenResponse:
    """Register new user with email."""
    auth_service = AuthService(db)

    # Validate secure request fields
    await validate_secure_request(
        request_data, redis, request_data.email, "registration"
    )

    # Verify the verification code
    verification_code = await auth_service.verify_verification_code(
        email=request_data.email,
        purpose="registration",
        code=request_data.verification_code,
    )

    # Register the user
    user = await auth_service.register_user(
        email=request_data.email,
        username=request_data.username,
        password=request_data.password,
        display_name=request_data.display_name,
    )

    # Mark verification code as used
    await auth_service.mark_code_used(verification_code)

    await db.commit()

    return _create_token_response(user)


# === Login Routes ===


@public_router.post(
    "/login/password",
    response_model=AuthTokenResponse,
    summary="Login with password",
    description="Authenticate user with email and password.",
)
async def login_with_password(
    request_data: PasswordLoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis, Depends(get_redis)],
) -> AuthTokenResponse:
    """Login with email and password."""
    auth_service = AuthService(db)

    # Validate secure request fields
    await validate_secure_request(request_data, redis, request_data.email, "password")

    # Authenticate user
    user = await auth_service.authenticate_by_password(
        email=request_data.email,
        password=request_data.password,
    )

    await db.commit()

    return _create_token_response(user)


@public_router.post(
    "/login/verification-code",
    response_model=AuthTokenResponse,
    summary="Login with verification code",
    description="Authenticate user with email and verification code (passwordless).",
)
async def login_with_verification_code(
    request_data: VerificationCodeLoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis, Depends(get_redis)],
) -> AuthTokenResponse:
    """Login with email and verification code."""
    auth_service = AuthService(db)

    # Validate secure request fields
    await validate_secure_request(request_data, redis, request_data.email, "login")

    # Authenticate user
    user = await auth_service.authenticate_by_verification_code(
        email=request_data.email,
        code=request_data.verification_code,
    )

    await db.commit()

    return _create_token_response(user)


# === Password Routes ===


@public_router.post(
    "/password/reset",
    response_model=ResetPasswordResponse,
    summary="Reset password",
    description="Reset password using email verification code.",
)
async def reset_password(
    request_data: ResetPasswordRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis, Depends(get_redis)],
) -> ResetPasswordResponse:
    """Reset password with verification code."""
    auth_service = AuthService(db)

    # Validate secure request fields
    await validate_secure_request(
        request_data, redis, request_data.email, "password_reset"
    )

    # Reset password
    reset_at = await auth_service.reset_password(
        email=request_data.email,
        code=request_data.verification_code,
        new_password=request_data.new_password,
    )

    await db.commit()

    return ResetPasswordResponse(reset_at=reset_at)


@protected_router.post(
    "/password/change",
    response_model=ChangePasswordResponse,
    summary="Change password",
    description="Change password for authenticated user.",
)
async def change_password(
    request_data: ChangePasswordRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> ChangePasswordResponse:
    """Change password for logged-in user."""
    changed_at = await auth_service.change_password(
        user_id=current_user.id,
        current_password=request_data.current_password,
        new_password=request_data.new_password,
    )

    await auth_service.db.commit()

    return ChangePasswordResponse(changed_at=changed_at)


# === Email Binding Routes ===


@protected_router.post(
    "/email/bind",
    response_model=BindEmailResponse,
    summary="Bind email",
    description="Bind email to OAuth user account.",
)
async def bind_email(
    request_data: BindEmailRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis, Depends(get_redis)],
) -> BindEmailResponse:
    """Bind email to OAuth user account."""
    auth_service = AuthService(db)

    # Validate secure request fields
    await validate_secure_request(
        request_data, redis, request_data.email, "email_binding"
    )

    # Bind email
    email_verified_at = await auth_service.bind_email(
        user_id=current_user.id,
        email=request_data.email,
        code=request_data.verification_code,
        password=request_data.password,
    )

    await db.commit()

    return BindEmailResponse(
        email=request_data.email,
        email_verified_at=email_verified_at,
    )


@protected_router.post(
    "/email/change/verify-identity",
    response_model=VerifyIdentityResponse,
    summary="Verify identity for email change",
    description="Verify identity before changing email address.",
)
async def verify_identity_for_email_change(
    request_data: VerifyIdentityRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> VerifyIdentityResponse:
    """Verify identity before email change."""
    change_token = await auth_service.verify_identity_for_email_change(
        user_id=current_user.id,
        method=request_data.method,
        password=request_data.password,
        verification_code=request_data.verification_code,
    )

    await auth_service.db.commit()

    return VerifyIdentityResponse(
        change_token=change_token,
        expires_in=auth_settings.CHANGE_TOKEN_EXPIRE_MINUTES * 60,
    )


@protected_router.post(
    "/email/change/confirm",
    response_model=ConfirmEmailChangeResponse,
    summary="Confirm email change",
    description="Confirm email change with new email verification code.",
)
async def confirm_email_change(
    request_data: ConfirmEmailChangeRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis, Depends(get_redis)],
) -> ConfirmEmailChangeResponse:
    """Confirm email change."""
    auth_service = AuthService(db)

    # Validate secure request fields
    await validate_secure_request(
        request_data, redis, request_data.new_email, "email_change"
    )

    # Confirm email change
    old_email, new_email, changed_at = await auth_service.confirm_email_change(
        user_id=current_user.id,
        change_token=request_data.change_token,
        new_email=request_data.new_email,
        code=request_data.verification_code,
    )

    await db.commit()

    return ConfirmEmailChangeResponse(
        old_email=old_email,
        new_email=new_email,
        changed_at=changed_at,
    )
