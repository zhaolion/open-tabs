"""
Authentication business logic service.
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from tabapi.app.modules.auth.enums import AuthProviderType, UserStatus
from tabapi.app.modules.auth.exceptions import (
    EmailAlreadyBoundException,
    EmailAlreadyRegisteredException,
    InvalidChangeTokenException,
    InvalidCredentialsException,
    InvalidVerificationCodeException,
    NoEmailAuthenticationException,
    SamePasswordException,
    TooManyVerificationAttemptsException,
    UsernameAlreadyTakenException,
    UserNotFoundException,
    UserSuspendedException,
    VerificationCodeExpiredException,
)
from tabapi.app.modules.auth.models import User, UserAuthentication, VerificationCode
from tabapi.app.modules.auth.utils.jwt import create_change_token, decode_token
from tabapi.app.modules.auth.utils.password import hash_password, verify_password
from tabapi.app.modules.auth.utils.uid import generate_uid
from tabapi.app.modules.auth.utils.verification import (
    generate_verification_code,
    get_expiry_minutes,
    hash_verification_code,
    verify_code,
)


class AuthService:
    """
    Authentication business logic service.
    Handles all authentication-related operations.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # === User Lookup Operations ===

    async def get_user_by_email(self, email: str) -> User | None:
        """Get user by email (case-insensitive)."""
        stmt = select(User).where(func.lower(User.email) == email.lower())
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: int) -> User | None:
        """Get user by ID."""
        return await self.db.get(User, user_id)

    async def get_user_by_uid(self, uid: str) -> User | None:
        """Get user by UID."""
        stmt = select(User).where(User.uid == uid)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def is_email_registered(self, email: str) -> bool:
        """Check if email is already registered."""
        user = await self.get_user_by_email(email)
        return user is not None

    async def is_username_taken(self, username: str) -> bool:
        """Check if username is already taken."""
        stmt = select(User).where(func.lower(User.username) == username.lower())
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    # === Verification Code Operations ===

    async def create_verification_code(
        self,
        email: str,
        purpose: str,
        user_id: int | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> tuple[str, VerificationCode]:
        """
        Create a new verification code.

        Returns:
            Tuple of (plain_code, verification_code_record)
        """
        # Invalidate existing codes for same email + purpose
        await self._invalidate_existing_codes(email, purpose)

        # Generate new code
        plain_code = generate_verification_code()
        hashed_code = hash_verification_code(plain_code)
        expiry_minutes = get_expiry_minutes(purpose)

        verification_code = VerificationCode(
            user_id=user_id,
            email=email,
            code=hashed_code,
            purpose=purpose,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=expiry_minutes),
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.db.add(verification_code)
        await self.db.flush()

        return plain_code, verification_code

    async def verify_verification_code(
        self,
        email: str,
        purpose: str,
        code: str,
    ) -> VerificationCode:
        """
        Verify a verification code.

        Raises:
            InvalidVerificationCodeException: If code is invalid.
            VerificationCodeExpiredException: If code has expired.
            TooManyVerificationAttemptsException: If max attempts exceeded.
        """
        stmt = (
            select(VerificationCode)
            .where(
                and_(
                    func.lower(VerificationCode.email) == email.lower(),
                    VerificationCode.purpose == purpose,
                    VerificationCode.used_at.is_(None),
                )
            )
            .order_by(VerificationCode.created_at.desc())
        )
        result = await self.db.execute(stmt)
        verification_code = result.scalar_one_or_none()

        if not verification_code:
            raise InvalidVerificationCodeException()

        # Check expiration
        if verification_code.expires_at < datetime.now(timezone.utc):
            raise VerificationCodeExpiredException()

        # Check max attempts
        if verification_code.attempts >= verification_code.max_attempts:
            raise TooManyVerificationAttemptsException()

        # Verify code
        if not verify_code(code, verification_code.code):
            verification_code.attempts += 1
            await self.db.flush()
            raise InvalidVerificationCodeException()

        return verification_code

    async def mark_code_used(self, verification_code: VerificationCode) -> None:
        """Mark a verification code as used."""
        verification_code.used_at = datetime.now(timezone.utc)
        await self.db.flush()

    async def _invalidate_existing_codes(self, email: str, purpose: str) -> None:
        """Invalidate all existing unused codes for email + purpose."""
        stmt = select(VerificationCode).where(
            and_(
                func.lower(VerificationCode.email) == email.lower(),
                VerificationCode.purpose == purpose,
                VerificationCode.used_at.is_(None),
            )
        )
        result = await self.db.execute(stmt)
        for code in result.scalars().all():
            code.used_at = datetime.now(timezone.utc)
        await self.db.flush()

    # === Registration ===

    async def register_user(
        self,
        email: str,
        username: str,
        password: str,
        display_name: str | None = None,
    ) -> User:
        """
        Register a new user with email authentication.

        Raises:
            EmailAlreadyRegisteredException: If email is taken.
            UsernameAlreadyTakenException: If username is taken.
        """
        if await self.is_email_registered(email):
            raise EmailAlreadyRegisteredException()
        if await self.is_username_taken(username):
            raise UsernameAlreadyTakenException()

        # Create user
        user = User(
            uid=generate_uid(),
            email=email,
            username=username,
            display_name=display_name or username,
            status=UserStatus.ACTIVE.value,
            email_verified_at=datetime.now(timezone.utc),
        )
        self.db.add(user)
        await self.db.flush()

        # Create email authentication
        auth = UserAuthentication(
            user_id=user.id,
            provider_type=AuthProviderType.EMAIL.value,
            provider_user_id=email,
            password_hash=hash_password(password),
            is_primary=True,
        )
        self.db.add(auth)
        await self.db.flush()

        return user

    # === Login ===

    async def authenticate_by_password(self, email: str, password: str) -> User:
        """
        Authenticate user by email and password.

        Raises:
            InvalidCredentialsException: If credentials are invalid.
            UserSuspendedException: If user is suspended.
        """
        user = await self.get_user_by_email(email)
        if not user:
            # Prevent timing attacks by still running hash comparison
            verify_password(password, hash_password("dummy"))
            raise InvalidCredentialsException()

        if user.status == UserStatus.SUSPENDED.value:
            raise UserSuspendedException()
        if user.status == UserStatus.DELETED.value:
            raise InvalidCredentialsException()

        # Get email authentication
        auth = await self._get_email_authentication(user.id)
        if not auth or not auth.password_hash:
            raise InvalidCredentialsException()

        if not verify_password(password, auth.password_hash):
            raise InvalidCredentialsException()

        # Update last used timestamp
        auth.last_used_at = datetime.now(timezone.utc)
        await self.db.flush()

        return user

    async def authenticate_by_verification_code(
        self,
        email: str,
        code: str,
    ) -> User:
        """
        Authenticate user by email and verification code.

        Raises:
            UserNotFoundException: If user not found.
            UserSuspendedException: If user is suspended.
            InvalidVerificationCodeException: If code is invalid.
        """
        user = await self.get_user_by_email(email)
        if not user:
            raise UserNotFoundException()

        if user.status == UserStatus.SUSPENDED.value:
            raise UserSuspendedException()

        verification_code = await self.verify_verification_code(email, "login", code)
        await self.mark_code_used(verification_code)

        return user

    # === Password Operations ===

    async def reset_password(
        self,
        email: str,
        code: str,
        new_password: str,
    ) -> datetime:
        """
        Reset password using verification code.

        Raises:
            UserNotFoundException: If user not found.
            InvalidVerificationCodeException: If code is invalid.
            NoEmailAuthenticationException: If no email auth method.
        """
        user = await self.get_user_by_email(email)
        if not user:
            raise UserNotFoundException()

        verification_code = await self.verify_verification_code(
            email, "password_reset", code
        )

        auth = await self._get_email_authentication(user.id)
        if not auth:
            raise NoEmailAuthenticationException()

        auth.password_hash = hash_password(new_password)
        auth.last_used_at = datetime.now(timezone.utc)
        await self.mark_code_used(verification_code)
        await self.db.flush()

        return datetime.now(timezone.utc)

    async def change_password(
        self,
        user_id: int,
        current_password: str,
        new_password: str,
    ) -> datetime:
        """
        Change password for authenticated user.

        Raises:
            NoEmailAuthenticationException: If no email auth method.
            InvalidCredentialsException: If current password is wrong.
            SamePasswordException: If new password is same as current.
        """
        auth = await self._get_email_authentication(user_id)
        if not auth or not auth.password_hash:
            raise NoEmailAuthenticationException()

        if not verify_password(current_password, auth.password_hash):
            raise InvalidCredentialsException()

        if verify_password(new_password, auth.password_hash):
            raise SamePasswordException()

        auth.password_hash = hash_password(new_password)
        await self.db.flush()

        return datetime.now(timezone.utc)

    # === Email Binding ===

    async def bind_email(
        self,
        user_id: int,
        email: str,
        code: str,
        password: str | None = None,
    ) -> datetime:
        """
        Bind email to OAuth user.

        Raises:
            UserNotFoundException: If user not found.
            EmailAlreadyBoundException: If user already has email.
            EmailAlreadyRegisteredException: If email is taken by another user.
            InvalidVerificationCodeException: If code is invalid.
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundException()

        if user.email and user.email_verified_at:
            raise EmailAlreadyBoundException()

        if await self.is_email_registered(email):
            raise EmailAlreadyRegisteredException()

        verification_code = await self.verify_verification_code(
            email, "email_binding", code
        )

        # Update user email
        user.email = email
        user.email_verified_at = datetime.now(timezone.utc)

        # Create email authentication if password provided
        if password:
            auth = UserAuthentication(
                user_id=user.id,
                provider_type=AuthProviderType.EMAIL.value,
                provider_user_id=email,
                password_hash=hash_password(password),
                is_primary=False,
            )
            self.db.add(auth)

        await self.mark_code_used(verification_code)
        await self.db.flush()

        return user.email_verified_at

    async def verify_identity_for_email_change(
        self,
        user_id: int,
        method: str,
        password: str | None = None,
        verification_code: str | None = None,
    ) -> str:
        """
        Verify identity before email change.

        Returns:
            Change token for completing email change.

        Raises:
            InvalidCredentialsException: If password is wrong.
            InvalidVerificationCodeException: If code is invalid.
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundException()

        if method == "password":
            if not password:
                raise InvalidCredentialsException()
            auth = await self._get_email_authentication(user_id)
            if not auth or not verify_password(password, auth.password_hash):
                raise InvalidCredentialsException()
        elif method == "verification_code":
            if not verification_code:
                raise InvalidVerificationCodeException()
            vc = await self.verify_verification_code(
                user.email, "email_change", verification_code
            )
            await self.mark_code_used(vc)

        # Generate change token
        return create_change_token(user_id, "email_change")

    async def confirm_email_change(
        self,
        user_id: int,
        change_token: str,
        new_email: str,
        code: str,
    ) -> tuple[str, str, datetime]:
        """
        Confirm email change.

        Returns:
            Tuple of (old_email, new_email, changed_at)

        Raises:
            InvalidChangeTokenException: If token is invalid.
            EmailAlreadyRegisteredException: If email is taken.
            InvalidVerificationCodeException: If code is invalid.
        """
        # Verify change token
        try:
            payload = decode_token(change_token)
            if (
                payload.get("type") != "change"
                or payload.get("purpose") != "email_change"
            ):
                raise InvalidChangeTokenException()
            if int(payload.get("sub", 0)) != user_id:
                raise InvalidChangeTokenException()
        except Exception:
            raise InvalidChangeTokenException()

        user = await self.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundException()

        if await self.is_email_registered(new_email):
            raise EmailAlreadyRegisteredException()

        verification_code = await self.verify_verification_code(
            new_email, "email_change", code
        )

        old_email = user.email
        user.email = new_email
        user.email_verified_at = datetime.now(timezone.utc)

        # Update email authentication provider_user_id
        auth = await self._get_email_authentication(user_id)
        if auth:
            auth.provider_user_id = new_email

        await self.mark_code_used(verification_code)
        await self.db.flush()

        return old_email, new_email, user.email_verified_at

    # === Helper Methods ===

    async def _get_email_authentication(
        self,
        user_id: int,
    ) -> UserAuthentication | None:
        """Get email authentication for user."""
        stmt = select(UserAuthentication).where(
            and_(
                UserAuthentication.user_id == user_id,
                UserAuthentication.provider_type == AuthProviderType.EMAIL.value,
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
