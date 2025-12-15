"""
Authentication module configuration.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class AuthConfig(BaseSettings):
    """
    Authentication configuration settings.
    All settings can be overridden via environment variables with AUTH_ prefix.
    """

    model_config = SettingsConfigDict(
        extra="ignore",
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="AUTH_",
    )

    # JWT Settings
    JWT_SECRET: str = "change-me-in-production-use-a-strong-secret-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 604800  # 7 days
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Verification Code Settings
    VERIFICATION_CODE_LENGTH: int = 6
    VERIFICATION_CODE_EXPIRE_MINUTES: int = 10
    VERIFICATION_CODE_LOGIN_EXPIRE_MINUTES: int = 5
    VERIFICATION_CODE_MAX_ATTEMPTS: int = 5

    # Password Settings
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_MAX_LENGTH: int = 128
    BCRYPT_ROUNDS: int = 12

    # Change Token Settings (for email change flow)
    CHANGE_TOKEN_EXPIRE_MINUTES: int = 10

    # Signature Settings (for anti-replay attack)
    SIGNATURE_SECRET: str = "change-me-in-production-signature-key"
    AUTH_TIMESTAMP_WINDOW_SECONDS: int = 300  # 5 minutes
    NONCE_TTL_SECONDS: int = 600  # 10 minutes


# Global auth settings instance
auth_settings = AuthConfig()
