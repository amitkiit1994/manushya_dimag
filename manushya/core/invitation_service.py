"""
Invitation service for Manushya.ai
"""

import secrets
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from manushya.db.models import Identity, Invitation
from manushya.core.exceptions import ConflictError
from manushya.services.email_service import EmailService


class InvitationService:
    """Service for managing user invitations."""

    @staticmethod
    def generate_invitation_token() -> str:
        """Generate a secure invitation token."""
        return f"inv_{secrets.token_urlsafe(32)}"

    @staticmethod
    def calculate_expiration(days: int = 7) -> datetime:
        """Calculate invitation expiration date."""
        return datetime.utcnow() + timedelta(days=days)

    @staticmethod
    async def create_invitation(
        db: AsyncSession,
        email: str,
        role: str,
        claims: dict,
        tenant_id: str,
        invited_by: str | None = None,
        expires_in_days: int = 7,
    ) -> Invitation:
        """Create a new invitation."""
        # Check if invitation already exists for this email and tenant
        stmt = select(Invitation).where(
            Invitation.email == email,
            Invitation.tenant_id == tenant_id,
            ~Invitation.is_accepted,
        )
        result = await db.execute(stmt)
        existing_invitation = result.scalar_one_or_none()
        if existing_invitation and existing_invitation.is_valid:
            raise ValueError(f"Active invitation already exists for {email}")
        if existing_invitation and existing_invitation.status == "pending":
            raise ConflictError(
                "A pending invitation already exists for this email or external_id"
            )
        if existing_invitation and existing_invitation.status == "accepted":
            raise ConflictError(
                "This invitation has already been accepted"
            )
        # Generate token and expiration
        token = InvitationService.generate_invitation_token()
        expires_at = InvitationService.calculate_expiration(expires_in_days)
        # Create invitation
        invitation = Invitation(
            email=email,
            role=role,
            claims=claims,
            token=token,
            invited_by=invited_by,
            tenant_id=tenant_id,
            expires_at=expires_at,
        )
        db.add(invitation)
        await db.commit()
        await db.refresh(invitation)
        # Send invitation email
        try:
            email_content = InvitationService.generate_invitation_email_content(
                invitation=invitation,
                base_url="http://localhost:8000",  # This should come from settings
                tenant_name="Your Organization",  # This should come from tenant
            )
            await EmailService.send_invitation_email(
                to_email=invitation.email,
                subject=email_content["subject"],
                html_content=email_content["html"],
                text_content=email_content["text"],
            )
        except Exception as e:
            # Log error but don't fail the invitation creation
            import structlog

            logger = structlog.get_logger()
            logger.error("Failed to send invitation email", error=str(e))
        return invitation

    @staticmethod
    async def get_invitation_by_token(
        db: AsyncSession, token: str
    ) -> Invitation | None:
        """Get invitation by token."""
        stmt = select(Invitation).where(Invitation.token == token)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def validate_invitation(db: AsyncSession, token: str) -> Invitation | None:
        """Validate invitation token and return invitation if valid."""
        invitation = await InvitationService.get_invitation_by_token(db, token)
        if not invitation:
            return None
        if not invitation.is_valid:
            return None
        return invitation

    @staticmethod
    async def accept_invitation(
        db: AsyncSession, invitation: Invitation, external_id: str
    ) -> Identity:
        """Accept an invitation and create the identity."""
        if not invitation.is_valid:
            raise ValueError("Invitation is not valid")
        # Create the identity
        identity = Identity(
            external_id=external_id,
            role=invitation.role,
            claims=invitation.claims,
            tenant_id=invitation.tenant_id,
            is_active=True,
        )
        db.add(identity)
        # Mark invitation as accepted
        invitation.is_accepted = True
        invitation.accepted_at = datetime.utcnow()
        await db.commit()
        await db.refresh(identity)
        return identity

    @staticmethod
    async def get_invitations_by_tenant(
        db: AsyncSession, tenant_id: str, include_accepted: bool = False
    ) -> list[Invitation]:
        """Get all invitations for a tenant."""
        stmt = select(Invitation).where(Invitation.tenant_id == tenant_id)
        if not include_accepted:
            stmt = stmt.where(~Invitation.is_accepted)
        stmt = stmt.order_by(Invitation.created_at.desc())
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def revoke_invitation(db: AsyncSession, invitation_id: str) -> bool:
        """Revoke an invitation by deleting it."""
        stmt = select(Invitation).where(Invitation.id == invitation_id)
        result = await db.execute(stmt)
        invitation = result.scalar_one_or_none()
        if not invitation:
            return False
        await db.delete(invitation)
        await db.commit()
        return True

    @staticmethod
    def generate_invitation_email_content(
        invitation: Invitation, base_url: str, tenant_name: str
    ) -> dict[str, str]:
        """Generate email content for invitation."""
        invitation_url = f"{base_url}/v1/invitations/accept?token={invitation.token}"
        subject = f"Invitation to join {tenant_name} on Manushya.ai"
        html_content = f"""
        <html>
        <body>
            <h2>You've been invited to join {tenant_name}</h2>
            <p>You have been invited to join {tenant_name} on Manushya.ai with the role: <strong>{invitation.role}</strong></p>
            <p>Click the link below to accept your invitation:</p>
            <p><a href="{invitation_url}">Accept Invitation</a></p>
            <p>This invitation expires on {invitation.expires_at.strftime('%Y-%m-%d %H:%M UTC')}</p>
            <p>If you have any questions, please contact your administrator.</p>
        </body>
        </html>
        """
        text_content = f"""
        You've been invited to join {tenant_name}
        You have been invited to join {tenant_name} on Manushya.ai with the role: {invitation.role}
        Click the link below to accept your invitation:
        {invitation_url}
        This invitation expires on {invitation.expires_at.strftime('%Y-%m-%d %H:%M UTC')}
        If you have any questions, please contact your administrator.
        """
        return {"subject": subject, "html": html_content, "text": text_content}
