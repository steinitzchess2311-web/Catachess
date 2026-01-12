"""
Resend email service for sending verification codes and other emails
"""
import logging
from pathlib import Path
from typing import Optional

import resend

from core.config import settings

logger = logging.getLogger(__name__)

# Set Resend API key
resend.api_key = settings.RESEND_API_KEY

# Template directory
TEMPLATE_DIR = Path(__file__).parent.parent / "templates" / "emails"


class ResendEmailService:
    """Service for sending emails via Resend"""

    @staticmethod
    def _load_template(template_name: str) -> str:
        """Load an email template from file"""
        template_path = TEMPLATE_DIR / template_name
        try:
            with open(template_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            logger.error(f"Email template not found: {template_path}")
            raise

    @staticmethod
    def _render_template(template: str, **kwargs) -> str:
        """Simple template rendering by replacing {variable} placeholders"""
        rendered = template
        for key, value in kwargs.items():
            rendered = rendered.replace(f"{{{key}}}", str(value))
        return rendered

    @staticmethod
    async def send_verification_code(
        to_email: str,
        code: str,
        username: Optional[str] = None,
    ) -> bool:
        """
        Send a verification code email

        Args:
            to_email: Recipient email address
            code: Verification code (plain text, not hashed)
            username: Optional username for personalization

        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            # Load templates
            html_template = ResendEmailService._load_template("signup_code.html")
            text_template = ResendEmailService._load_template("signup_code.txt")

            # Render templates
            template_vars = {
                "code": code,
                "username": username or "User",
                "expire_minutes": settings.VERIFICATION_CODE_EXPIRE_MINUTES,
            }

            html_content = ResendEmailService._render_template(html_template, **template_vars)
            text_content = ResendEmailService._render_template(text_template, **template_vars)

            # Send email via Resend
            params = {
                "from": settings.RESEND_FROM_EMAIL,
                "to": [to_email],
                "subject": "Your CataChess Verification Code",
                "html": html_content,
                "text": text_content,
            }

            response = resend.Emails.send(params)

            logger.info(
                f"Verification email sent successfully",
                extra={
                    "email_id": response.get("id"),
                    "to_email_domain": to_email.split("@")[1],  # Log domain only for privacy
                }
            )
            return True

        except Exception as e:
            logger.error(
                f"Failed to send verification email: {str(e)}",
                extra={"to_email_domain": to_email.split("@")[1] if "@" in to_email else "unknown"},
                exc_info=True,
            )
            return False

    @staticmethod
    async def send_password_reset_code(
        to_email: str,
        code: str,
        username: Optional[str] = None,
    ) -> bool:
        """
        Send a password reset code email (placeholder for future implementation)

        Args:
            to_email: Recipient email address
            code: Reset code (plain text, not hashed)
            username: Optional username for personalization

        Returns:
            True if email sent successfully, False otherwise
        """
        # TODO: Implement password reset email when needed
        logger.warning("Password reset email not yet implemented")
        return False
