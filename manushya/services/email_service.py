"""
Email service for Manushya.ai
"""

from typing import Any

import structlog

logger = structlog.get_logger()


class EmailService:
    """Email service for sending notifications."""

    @staticmethod
    async def send_invitation_email(
        to_email: str, subject: str, html_content: str, text_content: str, **kwargs: Any
    ) -> bool:
        """
        Send an invitation email.
        In production, this would integrate with services like:
        - SendGrid
        - AWS SES
        - Mailgun
        - SMTP server
        """
        try:
            # Log the email content for development
            logger.info(
                "Sending invitation email",
                to_email=to_email,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                **kwargs,
            )
            # In production, this would actually send the email
            # For now, we just log it
            logger.info(
                "Email would be sent in production", to_email=to_email, subject=subject
            )
            return True
        except Exception as e:
            logger.error(
                "Failed to send invitation email", to_email=to_email, error=str(e)
            )
            return False

    @staticmethod
    async def send_welcome_email(
        to_email: str, identity_id: str, tenant_name: str, **kwargs: Any
    ) -> bool:
        """Send a welcome email to newly created identities."""
        try:
            logger.info(
                "Sending welcome email",
                to_email=to_email,
                identity_id=identity_id,
                tenant_name=tenant_name,
                **kwargs,
            )
            return True
        except Exception as e:
            logger.error(
                "Failed to send welcome email", to_email=to_email, error=str(e)
            )
            return False
