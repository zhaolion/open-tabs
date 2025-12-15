"""
Verification code utilities.
"""

import hashlib
import secrets

from tabapi.app.modules.auth.config import auth_settings

# Verification code expiry by purpose (minutes)
VERIFICATION_CODE_EXPIRY: dict[str, int] = {
    "registration": 10,
    "login": 5,
    "password_reset": 10,
    "email_binding": 10,
    "email_change": 10,
}


def generate_verification_code(length: int | None = None) -> str:
    """
    Generate a cryptographically secure numeric verification code.

    Args:
        length: The length of the code. Defaults to config value.

    Returns:
        A numeric string of the specified length.
    """
    length = length or auth_settings.VERIFICATION_CODE_LENGTH
    return "".join(str(secrets.randbelow(10)) for _ in range(length))


def hash_verification_code(code: str) -> str:
    """
    Hash a verification code for secure storage using SHA-256.

    Args:
        code: The plain verification code.

    Returns:
        The SHA-256 hash of the code as a hex string.
    """
    return hashlib.sha256(code.encode()).hexdigest()


def verify_code(plain_code: str, hashed_code: str) -> bool:
    """
    Verify a code against its hash using constant-time comparison.

    Args:
        plain_code: The plain verification code to verify.
        hashed_code: The SHA-256 hashed code.

    Returns:
        True if the code matches, False otherwise.
    """
    return secrets.compare_digest(
        hash_verification_code(plain_code),
        hashed_code,
    )


def get_expiry_minutes(purpose: str) -> int:
    """
    Get the expiry time in minutes for a verification code purpose.

    Args:
        purpose: The purpose of the verification code.

    Returns:
        The expiry time in minutes.
    """
    return VERIFICATION_CODE_EXPIRY.get(
        purpose,
        auth_settings.VERIFICATION_CODE_EXPIRE_MINUTES,
    )
