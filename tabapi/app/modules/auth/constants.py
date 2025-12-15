"""
Authentication module constants and error codes.
"""

from enum import IntEnum


class ErrorCode(IntEnum):
    """
    Authentication error codes.

    Error code ranges:
    - 400xx: General errors
    - 401xx: Authentication errors
    - 429xx: Rate limiting errors
    """

    # General errors (400xx)
    INVALID_EMAIL_FORMAT = 40001
    EMAIL_ALREADY_REGISTERED = 40002
    EMAIL_NOT_FOUND = 40003
    USER_SUSPENDED = 40004
    USERNAME_ALREADY_TAKEN = 40005
    INVALID_VERIFICATION_CODE = 40006
    VERIFICATION_CODE_EXPIRED = 40007
    TOO_MANY_VERIFICATION_ATTEMPTS = 40008
    WEAK_PASSWORD = 40009
    EMAIL_ALREADY_BOUND = 40010
    NO_EMAIL_AUTHENTICATION = 40011
    INVALID_CHANGE_TOKEN = 40012
    SAME_PASSWORD = 40013
    INVALID_SIGNATURE = 40014
    TIMESTAMP_EXPIRED = 40015
    NONCE_ALREADY_USED = 40016

    # Authentication errors (401xx)
    INVALID_CREDENTIALS = 40101
    USER_NOT_FOUND = 40102
    USER_IS_SUSPENDED = 40103
    EMAIL_NOT_VERIFIED = 40104
    TOKEN_EXPIRED = 40105
    TOKEN_INVALID = 40106

    # Rate limiting errors (429xx)
    RATE_LIMIT_EXCEEDED = 42901
    ACCOUNT_TEMPORARILY_LOCKED = 42902
    IP_TEMPORARILY_BLOCKED = 42903


# Error code to message mapping
ERROR_MESSAGES: dict[ErrorCode, str] = {
    # General errors
    ErrorCode.INVALID_EMAIL_FORMAT: "Invalid email format",
    ErrorCode.EMAIL_ALREADY_REGISTERED: "Email already registered",
    ErrorCode.EMAIL_NOT_FOUND: "Email not found",
    ErrorCode.USER_SUSPENDED: "User account is suspended",
    ErrorCode.USERNAME_ALREADY_TAKEN: "Username already taken",
    ErrorCode.INVALID_VERIFICATION_CODE: "Invalid verification code",
    ErrorCode.VERIFICATION_CODE_EXPIRED: "Verification code has expired",
    ErrorCode.TOO_MANY_VERIFICATION_ATTEMPTS: "Too many verification attempts",
    ErrorCode.WEAK_PASSWORD: "Password does not meet strength requirements",
    ErrorCode.EMAIL_ALREADY_BOUND: "Email is already bound to this account",
    ErrorCode.NO_EMAIL_AUTHENTICATION: "No email authentication method set",
    ErrorCode.INVALID_CHANGE_TOKEN: "Invalid or expired change token",
    ErrorCode.SAME_PASSWORD: "New password must be different from current password",
    ErrorCode.INVALID_SIGNATURE: "Invalid request signature",
    ErrorCode.TIMESTAMP_EXPIRED: "Request timestamp has expired",
    ErrorCode.NONCE_ALREADY_USED: "Request nonce has already been used",
    # Authentication errors
    ErrorCode.INVALID_CREDENTIALS: "Invalid credentials",
    ErrorCode.USER_NOT_FOUND: "User not found",
    ErrorCode.USER_IS_SUSPENDED: "User account is suspended",
    ErrorCode.EMAIL_NOT_VERIFIED: "Email is not verified",
    ErrorCode.TOKEN_EXPIRED: "Token has expired",
    ErrorCode.TOKEN_INVALID: "Token is invalid",
    # Rate limiting errors
    ErrorCode.RATE_LIMIT_EXCEEDED: "Rate limit exceeded",
    ErrorCode.ACCOUNT_TEMPORARILY_LOCKED: "Account is temporarily locked",
    ErrorCode.IP_TEMPORARILY_BLOCKED: "IP is temporarily blocked",
}


def get_error_message(code: ErrorCode) -> str:
    """Get the error message for an error code."""
    return ERROR_MESSAGES.get(code, "Unknown error")
