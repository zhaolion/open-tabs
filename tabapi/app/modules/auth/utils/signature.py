"""
Request signature utilities for anti-replay attack protection.
"""

import hashlib
import hmac
import time

from tabapi.app.modules.auth.config import auth_settings


def generate_signature(
    email: str,
    nonce: str,
    auth_at: int,
    purpose: str,
) -> str:
    """
    Generate an HMAC-SHA256 signature for request validation.

    The signature is computed as:
    HMAC-SHA256(key=secret, message="{email}:{nonce}:{auth_at}:{purpose}")

    Args:
        email: The user's email address.
        nonce: A unique random string (UUID).
        auth_at: Unix timestamp of the request.
        purpose: The purpose of the operation.

    Returns:
        The hex-encoded signature string.
    """
    message = f"{email}:{nonce}:{auth_at}:{purpose}"
    signature = hmac.new(
        auth_settings.SIGNATURE_SECRET.encode(),
        message.encode(),
        hashlib.sha256,
    )
    return signature.hexdigest()


def verify_signature(
    email: str,
    nonce: str,
    auth_at: int,
    purpose: str,
    signature: str,
) -> bool:
    """
    Verify a request signature using constant-time comparison.

    Args:
        email: The user's email address.
        nonce: The unique random string from the request.
        auth_at: Unix timestamp from the request.
        purpose: The purpose of the operation.
        signature: The signature to verify.

    Returns:
        True if the signature is valid, False otherwise.
    """
    expected_signature = generate_signature(email, nonce, auth_at, purpose)
    return hmac.compare_digest(expected_signature, signature)


def validate_auth_timestamp(
    auth_at: int,
    window_seconds: int | None = None,
) -> bool:
    """
    Validate that the auth_at timestamp is within the allowed time window.

    Args:
        auth_at: Unix timestamp from the request.
        window_seconds: Maximum allowed time difference in seconds.

    Returns:
        True if the timestamp is valid, False otherwise.
    """
    window = window_seconds or auth_settings.AUTH_TIMESTAMP_WINDOW_SECONDS
    current_time = int(time.time())
    time_diff = abs(current_time - auth_at)
    return time_diff <= window
