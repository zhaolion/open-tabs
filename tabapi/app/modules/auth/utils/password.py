"""
Password hashing utilities using bcrypt.
"""

import bcrypt

from tabapi.app.modules.auth.config import auth_settings


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: The plain text password to hash.

    Returns:
        The bcrypt hashed password.
    """
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=auth_settings.BCRYPT_ROUNDS)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash using constant-time comparison.

    Args:
        plain_password: The plain text password to verify.
        hashed_password: The bcrypt hashed password.

    Returns:
        True if the password matches, False otherwise.
    """
    try:
        password_bytes = plain_password.encode("utf-8")
        hashed_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception:
        return False
