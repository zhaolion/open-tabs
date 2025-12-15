"""
Email service for sending verification codes.
Provides an abstract interface with a mock implementation for development.
"""

from tabapi.app.core.logger import get_logger
from abc import ABC, abstractmethod

from tabapi.app.core.config import settings

logger = get_logger(__name__)


class EmailService(ABC):
    """Abstract base class for email services."""

    @abstractmethod
    async def send_verification_code(
        self,
        email: str,
        code: str,
        purpose: str,
    ) -> bool:
        """
        Send a verification code email.

        Args:
            email: The recipient email address.
            code: The verification code to send.
            purpose: The purpose of the code (registration, login, etc.).

        Returns:
            True if the email was sent successfully, False otherwise.
        """
        pass


class MockEmailService(EmailService):
    """
    Mock email service for development and testing.
    Logs verification codes instead of sending actual emails.
    """

    async def send_verification_code(
        self,
        email: str,
        code: str,
        purpose: str,
    ) -> bool:
        """
        Log the verification code instead of sending an email.

        Args:
            email: The recipient email address.
            code: The verification code.
            purpose: The purpose of the code.

        Returns:
            Always returns True.
        """
        logger.info(
            "[MOCK EMAIL] Verification code sent | "
            f"To: {email} | Code: {code} | Purpose: {purpose}"
        )
        return True


# Email templates by purpose
EMAIL_SUBJECTS = {
    "registration": "[TabAPI] Your Registration Verification Code",
    "login": "[TabAPI] Your Login Verification Code",
    "password_reset": "[TabAPI] Your Password Reset Code",
    "email_binding": "[TabAPI] Your Email Binding Code",
    "email_change": "[TabAPI] Your Email Change Verification Code",
}


def get_email_service() -> EmailService:
    """
    Factory function to get the appropriate email service.

    Returns:
        MockEmailService in mock mode, or a real implementation otherwise.
    """
    if settings.EMAIL_MOCK_MODE:
        return MockEmailService()
    # TODO: Implement real email service (SMTP, SendGrid, etc.)
    return MockEmailService()
