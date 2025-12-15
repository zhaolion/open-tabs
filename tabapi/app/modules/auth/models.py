"""
Database models for the authentication module.
"""

from datetime import datetime
from typing import Any

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from tabapi.app.db.base import Base
from tabapi.app.db.deps import reference_col
from tabapi.app.db.mixins import BaseFeaturesMixin
from tabapi.app.modules.auth.enums import (
    AdminRole,
    AuthProviderType,
    UserStatus,
    VerificationCodePurpose,
)
from tabapi.app.modules.auth.utils.uid import generate_uid


class User(Base, BaseFeaturesMixin):
    """
    Core user table.

    Stores essential user identity information. Authentication credentials
    are stored separately in user_authentications table.
    """

    __tablename__ = "users"

    # External ID (Snowflake ID + Base62 encoded)
    uid: Mapped[str] = mapped_column(
        sa.String(16),
        unique=True,
        nullable=False,
        index=True,
        default=generate_uid,
        comment="External user ID (Base62 encoded Snowflake ID)",
    )

    # Core identity
    username: Mapped[str] = mapped_column(
        sa.String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="Unique username",
    )

    email: Mapped[str | None] = mapped_column(
        sa.String(255),
        unique=True,
        nullable=True,
        index=True,
        comment="Email address (nullable for OAuth users without email)",
    )

    # Profile information
    display_name: Mapped[str | None] = mapped_column(
        sa.String(100),
        nullable=True,
        comment="Display name (can differ from username)",
    )

    avatar_url: Mapped[str | None] = mapped_column(
        sa.String(500),
        nullable=True,
        comment="Avatar image URL",
    )

    # Account status (validated in application code via UserStatus enum)
    status: Mapped[str] = mapped_column(
        sa.String(20),
        nullable=False,
        default=UserStatus.PENDING.value,
        server_default=UserStatus.PENDING.value,
        index=True,
        comment="Account status: pending, active, suspended, deleted",
    )

    email_verified_at: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=True,
        comment="Email verification timestamp",
    )

    # Admin flag
    is_admin: Mapped[bool] = mapped_column(
        sa.Boolean,
        nullable=False,
        default=False,
        server_default=sa.text("false"),
        index=True,
        comment="Whether user has admin privileges",
    )

    # Extensible metadata
    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        default=dict,
        server_default=sa.text("'{}'::jsonb"),
        comment="Extensible user metadata",
    )

    # Soft delete
    deleted_at: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=True,
        comment="Soft delete timestamp",
    )

    # Relationships
    authentications = relationship(
        "UserAuthentication",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    verification_codes = relationship(
        "VerificationCode",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    admin_profile = relationship(
        "UserAdminProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        foreign_keys="UserAdminProfile.user_id",
    )

    __table_args__ = (
        sa.Index("idx_users_status_admin", "status", "is_admin"),
        sa.Index("idx_users_email_lower", sa.func.lower(email)),
    )

    @property
    def status_enum(self) -> UserStatus:
        """Get status as enum."""
        return UserStatus(self.status)

    @status_enum.setter
    def status_enum(self, value: UserStatus) -> None:
        """Set status from enum."""
        self.status = value.value


class UserAuthentication(Base, BaseFeaturesMixin):
    """
    User authentication methods table.

    Supports multiple authentication methods per user (email/password, OAuth).
    """

    __tablename__ = "user_authentications"

    # Foreign key to user
    user_id = reference_col(
        "users",
        nullable=False,
        ondelete="CASCADE",
        index=True,
    )

    # Provider information (validated in application code via AuthProviderType enum)
    provider_type = sa.Column(
        sa.String(20),
        nullable=False,
        comment="Authentication provider type: email, google, github",
    )

    provider_user_id = sa.Column(
        sa.String(255),
        nullable=False,
        comment="User ID from the provider (email for EMAIL type, OAuth ID for others)",
    )

    # Password hash (only for EMAIL provider)
    password_hash = sa.Column(
        sa.String(255),
        nullable=True,
        comment="Hashed password (only for EMAIL provider)",
    )

    # OAuth data
    provider_data = sa.Column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=sa.text("'{}'::jsonb"),
        comment="OAuth tokens and provider-specific data",
    )

    # Status
    is_primary = sa.Column(
        sa.Boolean,
        nullable=False,
        default=False,
        server_default=sa.text("false"),
        comment="Whether this is the primary authentication method",
    )

    last_used_at = sa.Column(
        sa.TIMESTAMP(timezone=True),
        nullable=True,
        comment="Last time this auth method was used",
    )

    # Relationship
    user = relationship("User", back_populates="authentications")

    __table_args__ = (
        # Unique constraint: one provider_user_id per provider type
        sa.UniqueConstraint(
            "provider_type",
            "provider_user_id",
            name="uq_auth_provider_user",
        ),
        # Index for login queries
        sa.Index(
            "idx_auth_provider_lookup",
            "provider_type",
            "provider_user_id",
        ),
        # Partial unique index: only one primary auth per user
        sa.Index(
            "idx_auth_user_primary",
            "user_id",
            unique=True,
            postgresql_where=sa.text("is_primary = true"),
        ),
    )

    @property
    def provider_type_enum(self) -> AuthProviderType:
        """Get provider_type as enum."""
        return AuthProviderType(self.provider_type)

    @provider_type_enum.setter
    def provider_type_enum(self, value: AuthProviderType) -> None:
        """Set provider_type from enum."""
        self.provider_type = value.value


class VerificationCode(Base, BaseFeaturesMixin):
    """
    Verification codes for various user operations.

    Supports registration, login, password reset, and sensitive operations.
    """

    __tablename__ = "verification_codes"

    # Foreign key to user (nullable for pre-registration)
    user_id = reference_col(
        "users",
        nullable=True,
        ondelete="CASCADE",
        index=True,
    )

    # Target email
    email = sa.Column(
        sa.String(255),
        nullable=False,
        index=True,
        comment="Target email address",
    )

    # Code information
    code = sa.Column(
        sa.String(64),
        nullable=False,
        comment="Hashed verification code (SHA-256, 64 hex chars)",
    )

    # Purpose (validated in application code via VerificationCodePurpose enum)
    purpose = sa.Column(
        sa.String(20),
        nullable=False,
        comment="Purpose: registration, login, password_reset, sensitive_op",
    )

    # Expiration and usage
    expires_at = sa.Column(
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        index=True,
        comment="Expiration timestamp",
    )

    used_at = sa.Column(
        sa.TIMESTAMP(timezone=True),
        nullable=True,
        comment="Timestamp when code was used",
    )

    # Security
    attempts = sa.Column(
        sa.Integer,
        nullable=False,
        default=0,
        server_default=sa.text("0"),
        comment="Number of verification attempts",
    )

    max_attempts = sa.Column(
        sa.Integer,
        nullable=False,
        default=5,
        server_default=sa.text("5"),
        comment="Maximum allowed attempts",
    )

    # Context
    ip_address = sa.Column(
        sa.String(45),
        nullable=True,
        comment="IP address that requested the code",
    )

    user_agent = sa.Column(
        sa.String(500),
        nullable=True,
        comment="User agent that requested the code",
    )

    context = sa.Column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=sa.text("'{}'::jsonb"),
        comment="Operation-specific context",
    )

    # Relationship
    user = relationship("User", back_populates="verification_codes")

    __table_args__ = (
        sa.Index("idx_vc_email_purpose", "email", "purpose"),
        sa.Index("idx_vc_code_lookup", "code", "purpose", "email"),
        # Partial index for active codes
        sa.Index(
            "idx_vc_active",
            "email",
            "purpose",
            postgresql_where=sa.text("used_at IS NULL"),
        ),
    )

    @property
    def purpose_enum(self) -> VerificationCodePurpose:
        """Get purpose as enum."""
        return VerificationCodePurpose(self.purpose)

    @purpose_enum.setter
    def purpose_enum(self, value: VerificationCodePurpose) -> None:
        """Set purpose from enum."""
        self.purpose = value.value


class UserAdminProfile(Base, BaseFeaturesMixin):
    """
    Admin-specific profile data.

    One-to-one relationship with User (only for admins).
    """

    __tablename__ = "user_admin_profiles"

    # Foreign key to user (one-to-one)
    user_id = reference_col(
        "users",
        nullable=False,
        ondelete="CASCADE",
    )

    # Admin role (validated in application code via AdminRole enum)
    role = sa.Column(
        sa.String(20),
        nullable=False,
        default=AdminRole.MODERATOR.value,
        server_default=AdminRole.MODERATOR.value,
        comment="Admin role: super_admin, admin, moderator",
    )

    # Permissions
    permissions = sa.Column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=sa.text("'{}'::jsonb"),
        comment="Granular permissions",
    )

    # Preferences
    preferences = sa.Column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=sa.text("'{}'::jsonb"),
        comment="Admin UI preferences",
    )

    # Activity tracking
    last_admin_action_at = sa.Column(
        sa.TIMESTAMP(timezone=True),
        nullable=True,
        comment="Last admin action timestamp",
    )

    # Notes
    notes = sa.Column(
        sa.Text,
        nullable=True,
        comment="Internal notes about this admin",
    )

    # Granted by
    granted_by_user_id = reference_col(
        "users",
        nullable=True,
        ondelete="SET NULL",
    )

    granted_at = sa.Column(
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sa.text("now()"),
        comment="When admin privileges were granted",
    )

    # Relationships
    user = relationship(
        "User",
        back_populates="admin_profile",
        foreign_keys=[user_id],
    )

    granted_by = relationship(
        "User",
        foreign_keys=[granted_by_user_id],
    )

    __table_args__ = (
        sa.UniqueConstraint("user_id", name="uq_admin_profile_user"),
        sa.Index("idx_admin_role", "role"),
        sa.Index("idx_admin_granted_by", "granted_by_user_id"),
    )

    @property
    def role_enum(self) -> AdminRole:
        """Get role as enum."""
        return AdminRole(self.role)

    @role_enum.setter
    def role_enum(self, value: AdminRole) -> None:
        """Set role from enum."""
        self.role = value.value


class OAuthProviderConfig(Base, BaseFeaturesMixin):
    """
    OAuth provider configuration.

    Stores OAuth provider settings for dynamic management.
    """

    __tablename__ = "oauth_provider_configs"

    # Provider type (validated in application code via AuthProviderType enum)
    provider = sa.Column(
        sa.String(20),
        nullable=False,
        unique=True,
        index=True,
        comment="OAuth provider type: email, google, github",
    )

    # Display information
    display_name = sa.Column(
        sa.String(100),
        nullable=False,
        comment="Display name for the provider",
    )

    icon_url = sa.Column(
        sa.String(500),
        nullable=True,
        comment="Icon URL for the provider",
    )

    # OAuth credentials
    client_id = sa.Column(
        sa.String(255),
        nullable=False,
        comment="OAuth Client ID",
    )

    client_secret_encrypted = sa.Column(
        sa.String(500),
        nullable=False,
        comment="Encrypted OAuth Client Secret",
    )

    # OAuth URLs
    authorization_url = sa.Column(
        sa.String(500),
        nullable=True,
        comment="OAuth authorization URL",
    )

    token_url = sa.Column(
        sa.String(500),
        nullable=True,
        comment="OAuth token URL",
    )

    userinfo_url = sa.Column(
        sa.String(500),
        nullable=True,
        comment="OAuth user info URL",
    )

    # Scopes
    default_scopes = sa.Column(
        JSONB,
        nullable=False,
        default=list,
        server_default=sa.text("'[]'::jsonb"),
        comment="Default OAuth scopes",
    )

    # Provider-specific configuration
    config = sa.Column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=sa.text("'{}'::jsonb"),
        comment="Provider-specific configuration",
    )

    # Status
    is_enabled = sa.Column(
        sa.Boolean,
        nullable=False,
        default=True,
        server_default=sa.text("true"),
        comment="Whether the provider is enabled",
    )

    __table_args__ = (sa.Index("idx_oauth_provider_enabled", "provider", "is_enabled"),)

    @property
    def provider_enum(self) -> AuthProviderType:
        """Get provider as enum."""
        return AuthProviderType(self.provider)

    @provider_enum.setter
    def provider_enum(self, value: AuthProviderType) -> None:
        """Set provider from enum."""
        self.provider = value.value
