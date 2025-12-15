"""
Authentication module custom exceptions.
"""

from fastapi import HTTPException, status

from tabapi.app.modules.auth.constants import ErrorCode, get_error_message


class AuthException(HTTPException):
    """
    Base exception for authentication module.
    Provides consistent error response format.
    """

    def __init__(
        self,
        code: ErrorCode,
        message: str | None = None,
        status_code: int = status.HTTP_400_BAD_REQUEST,
    ):
        self.code = code
        message = message or get_error_message(code)
        super().__init__(
            status_code=status_code,
            detail={"code": int(code), "message": message},
        )


# === General Exceptions (400xx) ===


class InvalidEmailFormatException(AuthException):
    """Raised when email format is invalid."""

    def __init__(self):
        super().__init__(code=ErrorCode.INVALID_EMAIL_FORMAT)


class EmailAlreadyRegisteredException(AuthException):
    """Raised when email is already registered."""

    def __init__(self):
        super().__init__(code=ErrorCode.EMAIL_ALREADY_REGISTERED)


class EmailNotFoundException(AuthException):
    """Raised when email is not found."""

    def __init__(self):
        super().__init__(
            code=ErrorCode.EMAIL_NOT_FOUND,
            status_code=status.HTTP_404_NOT_FOUND,
        )


class UsernameAlreadyTakenException(AuthException):
    """Raised when username is already taken."""

    def __init__(self):
        super().__init__(code=ErrorCode.USERNAME_ALREADY_TAKEN)


class InvalidVerificationCodeException(AuthException):
    """Raised when verification code is invalid."""

    def __init__(self):
        super().__init__(code=ErrorCode.INVALID_VERIFICATION_CODE)


class VerificationCodeExpiredException(AuthException):
    """Raised when verification code has expired."""

    def __init__(self):
        super().__init__(code=ErrorCode.VERIFICATION_CODE_EXPIRED)


class TooManyVerificationAttemptsException(AuthException):
    """Raised when too many verification attempts have been made."""

    def __init__(self):
        super().__init__(code=ErrorCode.TOO_MANY_VERIFICATION_ATTEMPTS)


class WeakPasswordException(AuthException):
    """Raised when password does not meet strength requirements."""

    def __init__(self, message: str | None = None):
        super().__init__(code=ErrorCode.WEAK_PASSWORD, message=message)


class EmailAlreadyBoundException(AuthException):
    """Raised when email is already bound to the account."""

    def __init__(self):
        super().__init__(code=ErrorCode.EMAIL_ALREADY_BOUND)


class NoEmailAuthenticationException(AuthException):
    """Raised when user has no email authentication method."""

    def __init__(self):
        super().__init__(code=ErrorCode.NO_EMAIL_AUTHENTICATION)


class InvalidChangeTokenException(AuthException):
    """Raised when change token is invalid or expired."""

    def __init__(self):
        super().__init__(code=ErrorCode.INVALID_CHANGE_TOKEN)


class SamePasswordException(AuthException):
    """Raised when new password is the same as current password."""

    def __init__(self):
        super().__init__(code=ErrorCode.SAME_PASSWORD)


class InvalidSignatureException(AuthException):
    """Raised when request signature is invalid."""

    def __init__(self):
        super().__init__(code=ErrorCode.INVALID_SIGNATURE)


class TimestampExpiredException(AuthException):
    """Raised when request timestamp has expired."""

    def __init__(self):
        super().__init__(code=ErrorCode.TIMESTAMP_EXPIRED)


class NonceAlreadyUsedException(AuthException):
    """Raised when nonce has already been used."""

    def __init__(self):
        super().__init__(code=ErrorCode.NONCE_ALREADY_USED)


# === Authentication Exceptions (401xx) ===


class InvalidCredentialsException(AuthException):
    """Raised when credentials are invalid."""

    def __init__(self):
        super().__init__(
            code=ErrorCode.INVALID_CREDENTIALS,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class UserNotFoundException(AuthException):
    """Raised when user is not found."""

    def __init__(self):
        super().__init__(
            code=ErrorCode.USER_NOT_FOUND,
            status_code=status.HTTP_404_NOT_FOUND,
        )


class UserSuspendedException(AuthException):
    """Raised when user account is suspended."""

    def __init__(self):
        super().__init__(
            code=ErrorCode.USER_IS_SUSPENDED,
            status_code=status.HTTP_403_FORBIDDEN,
        )


class EmailNotVerifiedException(AuthException):
    """Raised when email is not verified."""

    def __init__(self):
        super().__init__(
            code=ErrorCode.EMAIL_NOT_VERIFIED,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class TokenExpiredException(AuthException):
    """Raised when token has expired."""

    def __init__(self):
        super().__init__(
            code=ErrorCode.TOKEN_EXPIRED,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class TokenInvalidException(AuthException):
    """Raised when token is invalid."""

    def __init__(self):
        super().__init__(
            code=ErrorCode.TOKEN_INVALID,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


# === Rate Limiting Exceptions (429xx) ===


class RateLimitExceededException(AuthException):
    """Raised when rate limit is exceeded."""

    def __init__(self):
        super().__init__(
            code=ErrorCode.RATE_LIMIT_EXCEEDED,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )


class AccountTemporarilyLockedException(AuthException):
    """Raised when account is temporarily locked."""

    def __init__(self):
        super().__init__(
            code=ErrorCode.ACCOUNT_TEMPORARILY_LOCKED,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )


class IPTemporarilyBlockedException(AuthException):
    """Raised when IP is temporarily blocked."""

    def __init__(self):
        super().__init__(
            code=ErrorCode.IP_TEMPORARILY_BLOCKED,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )
