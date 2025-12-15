"""
Authentication module Pydantic schemas.
"""

import re
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


# === Security Fields Mixin ===


class SecureRequestMixin(BaseModel):
    """
    Mixin for requests requiring anti-replay protection.
    All secure endpoints should inherit from this.
    """

    nonce: str = Field(
        ...,
        min_length=32,
        max_length=64,
        description="Unique random string (UUID) for replay protection",
    )
    auth_at: int = Field(
        ...,
        description="Unix timestamp of the request",
    )
    signature: str = Field(
        ...,
        min_length=64,
        max_length=64,
        description="HMAC-SHA256 signature of the request",
    )


# === Password Validation ===

PASSWORD_PATTERN_LOWERCASE = re.compile(r"[a-z]")
PASSWORD_PATTERN_UPPERCASE = re.compile(r"[A-Z]")
PASSWORD_PATTERN_DIGIT = re.compile(r"\d")


def validate_password_strength(password: str) -> str:
    """Validate password meets strength requirements."""
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters")
    if not PASSWORD_PATTERN_LOWERCASE.search(password):
        raise ValueError("Password must contain at least one lowercase letter")
    if not PASSWORD_PATTERN_UPPERCASE.search(password):
        raise ValueError("Password must contain at least one uppercase letter")
    if not PASSWORD_PATTERN_DIGIT.search(password):
        raise ValueError("Password must contain at least one digit")
    return password


# === Verification Code Schemas ===


class SendVerificationCodeRequest(SecureRequestMixin):
    """Request to send a verification code."""

    email: EmailStr
    purpose: str = Field(
        ...,
        pattern="^(registration|login|password_reset|email_binding|email_change)$",
        description="Purpose of the verification code",
    )


class SendVerificationCodeResponse(BaseModel):
    """Response after sending verification code."""

    expires_in: int = Field(description="Verification code expiry in seconds")
    next_send_available_at: datetime = Field(
        description="Next available send time (UTC)"
    )


# === Registration Schemas ===


class EmailRegisterRequest(SecureRequestMixin):
    """Request to register with email."""

    email: EmailStr
    username: str = Field(
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="Username (alphanumeric, underscore, hyphen)",
    )
    password: str = Field(
        min_length=8,
        max_length=128,
        description="Password (8-128 chars, must include upper, lower, digit)",
    )
    verification_code: str = Field(
        min_length=6,
        max_length=6,
        pattern=r"^\d{6}$",
        description="6-digit verification code",
    )
    display_name: str | None = Field(
        default=None,
        max_length=100,
        description="Display name (optional)",
    )

    @field_validator("password", mode="after")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return validate_password_strength(v)


# === Login Schemas ===


class PasswordLoginRequest(SecureRequestMixin):
    """Request to login with password."""

    email: EmailStr
    password: str = Field(
        min_length=1,
        max_length=128,
        description="User password",
    )


class VerificationCodeLoginRequest(SecureRequestMixin):
    """Request to login with verification code."""

    email: EmailStr
    verification_code: str = Field(
        min_length=6,
        max_length=6,
        pattern=r"^\d{6}$",
        description="6-digit verification code",
    )


# === Password Reset/Change Schemas ===


class ResetPasswordRequest(SecureRequestMixin):
    """Request to reset password."""

    email: EmailStr
    verification_code: str = Field(
        min_length=6,
        max_length=6,
        pattern=r"^\d{6}$",
        description="6-digit verification code",
    )
    new_password: str = Field(
        min_length=8,
        max_length=128,
        description="New password",
    )

    @field_validator("new_password", mode="after")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return validate_password_strength(v)


class ResetPasswordResponse(BaseModel):
    """Response after password reset."""

    reset_at: datetime


class ChangePasswordRequest(BaseModel):
    """Request to change password (authenticated user)."""

    current_password: str = Field(
        min_length=1,
        max_length=128,
        description="Current password",
    )
    new_password: str = Field(
        min_length=8,
        max_length=128,
        description="New password",
    )

    @field_validator("new_password", mode="after")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return validate_password_strength(v)


class ChangePasswordResponse(BaseModel):
    """Response after password change."""

    changed_at: datetime


# === Email Binding Schemas ===


class BindEmailRequest(SecureRequestMixin):
    """Request to bind email (OAuth user)."""

    email: EmailStr
    verification_code: str = Field(
        min_length=6,
        max_length=6,
        pattern=r"^\d{6}$",
        description="6-digit verification code",
    )
    password: str | None = Field(
        default=None,
        min_length=8,
        max_length=128,
        description="Optional password to enable password login",
    )

    @field_validator("password", mode="after")
    @classmethod
    def validate_password(cls, v: str | None) -> str | None:
        if v is not None:
            return validate_password_strength(v)
        return v


class BindEmailResponse(BaseModel):
    """Response after email binding."""

    email: str
    email_verified_at: datetime


class VerifyIdentityRequest(BaseModel):
    """Request to verify identity before email change."""

    method: str = Field(
        ...,
        pattern="^(password|verification_code)$",
        description="Verification method",
    )
    password: str | None = Field(
        default=None,
        min_length=1,
        max_length=128,
        description="Current password (if method=password)",
    )
    verification_code: str | None = Field(
        default=None,
        min_length=6,
        max_length=6,
        pattern=r"^\d{6}$",
        description="Verification code (if method=verification_code)",
    )

    @model_validator(mode="after")
    def validate_credentials(self):
        if self.method == "password" and not self.password:
            raise ValueError("Password is required when method is password")
        if self.method == "verification_code" and not self.verification_code:
            raise ValueError(
                "Verification code is required when method is verification_code"
            )
        return self


class VerifyIdentityResponse(BaseModel):
    """Response after identity verification."""

    change_token: str = Field(description="Token for completing email change")
    expires_in: int = Field(description="Token expiry in seconds")


class ConfirmEmailChangeRequest(SecureRequestMixin):
    """Request to confirm email change."""

    change_token: str = Field(description="Token from identity verification")
    new_email: EmailStr
    verification_code: str = Field(
        min_length=6,
        max_length=6,
        pattern=r"^\d{6}$",
        description="6-digit verification code sent to new email",
    )


class ConfirmEmailChangeResponse(BaseModel):
    """Response after email change confirmation."""

    old_email: str
    new_email: str
    changed_at: datetime


# === User Response Schemas ===


class UserResponse(BaseModel):
    """User information response."""

    uid: str
    username: str
    email: str | None
    display_name: str | None
    avatar_url: str | None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AuthTokenResponse(BaseModel):
    """Authentication token response."""

    user: UserResponse
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Token expiry in seconds")
