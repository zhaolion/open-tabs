"""
Enum definitions for the authentication module.
"""

from enum import Enum


class AuthProviderType(str, Enum):
    """Authentication provider types."""

    EMAIL = "email"
    GOOGLE = "google"
    GITHUB = "github"


class VerificationCodePurpose(str, Enum):
    """Verification code purposes."""

    REGISTRATION = "registration"
    LOGIN = "login"
    PASSWORD_RESET = "password_reset"
    SENSITIVE_OP = "sensitive_op"


class UserStatus(str, Enum):
    """User account status."""

    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class AdminRole(str, Enum):
    """Admin role types."""

    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    MODERATOR = "moderator"
