"""
Invitation management endpoints for Manushya.ai
"""

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from manushya.core.auth import get_current_identity
from manushya.core.exceptions import NotFoundError
from manushya.core.invitation_service import InvitationService
from manushya.core.policy_engine import PolicyEngine
from manushya.db.database import get_db
from manushya.db.models import AuditLog, Identity, Invitation, Tenant
from manushya.services.webhook_service import WebhookService

router = APIRouter()


# Pydantic models
class InvitationCreate(BaseModel):
    email: EmailStr = Field(..., description="Email address to invite")
    role: str = Field(..., description="Role for the invited user")
    claims: dict[str, Any] = Field(default_factory=dict, description="Additional claims for the user")
    expires_in_days: int = Field(default=7, description="Invitation expiration in days")


class InvitationAccept(BaseModel):
    external_id: str = Field(..., description="External ID for the new identity")


class InvitationResponse(BaseModel):
    id: uuid.UUID
    email: str
    role: str
    claims: dict[str, Any]
    is_accepted: bool
    accepted_at: datetime | None
    expires_at: datetime
    created_at: datetime
    updated_at: datetime
    tenant_id: uuid.UUID
    invited_by: uuid.UUID | None = None

    class Config:
        from_attributes = True


class InvitationAcceptResponse(BaseModel):
    identity: dict[str, Any]
    token: str = Field(..., description="JWT token for the new identity")


@router.post("/", response_model=InvitationResponse)
async def create_invitation(
    invitation_data: InvitationCreate,
    current_identity: Identity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
):
    """Create a new invitation."""
    # Check permissions - only admins can create invitations
    policy_engine = PolicyEngine(db)
    await policy_engine.check_identity_access(
        current_identity, "write", target_role="admin"
    )

    # Ensure current identity has a tenant
    if not current_identity.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create invitations without a tenant"
        )

    try:
        invitation = await InvitationService.create_invitation(
            db=db,
            email=invitation_data.email,
            role=invitation_data.role,
            claims=invitation_data.claims,
            tenant_id=str(current_identity.tenant_id),
            invited_by=str(current_identity.id),
            expires_in_days=invitation_data.expires_in_days
        )

        # Create audit log
        audit_log = AuditLog(
            event_type="invitation.created",
            actor_id=current_identity.id,
            tenant_id=current_identity.tenant_id,
            after_state={
                "email": invitation.email,
                "role": invitation.role,
                "claims": invitation.claims,
                "expires_at": invitation.expires_at.isoformat(),
            },
        )
        db.add(audit_log)
        await db.commit()

        # Trigger webhook for invitation sent
        await WebhookService.trigger_webhook(
            db=db,
            event_type="invitation.sent",
            payload={
                "id": str(invitation.id),
                "email": invitation.email,
                "role": invitation.role,
                "claims": invitation.claims,
                "invited_by": str(invitation.invited_by),
                "tenant_id": str(invitation.tenant_id),
                "expires_at": invitation.expires_at.isoformat(),
                "created_at": invitation.created_at.isoformat()
            },
            tenant_id=str(current_identity.tenant_id)
        )

        return InvitationResponse.from_orm(invitation)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        ) from e


@router.get("/{invitation_id}", response_model=InvitationResponse)
async def get_invitation(
    invitation_id: uuid.UUID,
    current_identity: Identity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
):
    """Get invitation by ID."""
    # Check permissions
    policy_engine = PolicyEngine(db)
    await policy_engine.check_identity_access(
        current_identity, "read", target_role="admin"
    )

    stmt = select(Invitation).where(Invitation.id == invitation_id)
    # Tenant filtering
    if current_identity.tenant_id is not None:
        stmt = stmt.where(Invitation.tenant_id == current_identity.tenant_id)
    # else: global/system-level identity can see all

    result = await db.execute(stmt)
    invitation = result.scalar_one_or_none()

    if not invitation:
        raise NotFoundError("Invitation not found")

    return InvitationResponse.from_orm(invitation)


@router.get("/", response_model=list[InvitationResponse])
async def list_invitations(
    include_accepted: bool = Query(False, description="Include accepted invitations"),
    current_identity: Identity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
):
    """List invitations."""
    # Check permissions
    policy_engine = PolicyEngine(db)
    await policy_engine.check_identity_access(
        current_identity, "read", target_role="admin"
    )

    # Ensure current identity has a tenant
    if not current_identity.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot list invitations without a tenant"
        )

    invitations = await InvitationService.get_invitations_by_tenant(
        db=db,
        tenant_id=str(current_identity.tenant_id),
        include_accepted=include_accepted
    )

    return [InvitationResponse.from_orm(invitation) for invitation in invitations]


@router.delete("/{invitation_id}")
async def revoke_invitation(
    invitation_id: uuid.UUID,
    current_identity: Identity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
):
    """Revoke an invitation."""
    # Check permissions
    policy_engine = PolicyEngine(db)
    await policy_engine.check_identity_access(
        current_identity, "delete", target_role="admin"
    )

    # Get invitation first for audit logging
    stmt = select(Invitation).where(Invitation.id == invitation_id)
    # Tenant filtering
    if current_identity.tenant_id is not None:
        stmt = stmt.where(Invitation.tenant_id == current_identity.tenant_id)
    # else: global/system-level identity can see all

    result = await db.execute(stmt)
    invitation = result.scalar_one_or_none()

    if not invitation:
        raise NotFoundError("Invitation not found")

    # Store before state for audit
    before_state = {
        "email": invitation.email,
        "role": invitation.role,
        "claims": invitation.claims,
        "is_accepted": invitation.is_accepted,
        "expires_at": invitation.expires_at.isoformat(),
    }

    # Revoke invitation
    success = await InvitationService.revoke_invitation(db, str(invitation_id))

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke invitation"
        )

    # Create audit log
    audit_log = AuditLog(
        event_type="invitation.revoked",
        actor_id=current_identity.id,
        tenant_id=current_identity.tenant_id,
        before_state=before_state,
    )
    db.add(audit_log)
    await db.commit()

    return {"message": "Invitation revoked successfully"}


@router.get("/validate/{token}")
async def validate_invitation_token(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """Validate an invitation token."""
    invitation = await InvitationService.validate_invitation(db, token)

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or expired invitation token"
        )

    # Get tenant name
    stmt = select(Tenant).where(Tenant.id == invitation.tenant_id)
    result = await db.execute(stmt)
    tenant = result.scalar_one_or_none()

    return {
        "valid": True,
        "email": invitation.email,
        "role": invitation.role,
        "tenant_name": tenant.name if tenant else "Unknown",
        "expires_at": invitation.expires_at.isoformat(),
    }


@router.post("/accept/{token}", response_model=InvitationAcceptResponse)
async def accept_invitation(
    token: str,
    accept_data: InvitationAccept,
    db: AsyncSession = Depends(get_db),
):
    """Accept an invitation and create identity."""
    # Validate invitation
    invitation = await InvitationService.validate_invitation(db, token)

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or expired invitation token"
        )

    try:
        # Accept invitation and create identity
        identity = await InvitationService.accept_invitation(
            db=db,
            invitation=invitation,
            external_id=accept_data.external_id
        )

        # Create audit log
        audit_log = AuditLog(
            event_type="invitation.accepted",
            actor_id=identity.id,
            tenant_id=identity.tenant_id,
            after_state={
                "email": invitation.email,
                "role": identity.role,
                "external_id": identity.external_id,
                "claims": identity.claims,
            },
        )
        db.add(audit_log)
        await db.commit()

        # Trigger webhook for invitation accepted
        await WebhookService.trigger_webhook(
            db=db,
            event_type="invitation.accepted",
            payload={
                "invitation_id": str(invitation.id),
                "identity_id": str(identity.id),
                "email": invitation.email,
                "role": identity.role,
                "external_id": identity.external_id,
                "tenant_id": str(identity.tenant_id),
                "accepted_at": datetime.utcnow().isoformat()
            },
            tenant_id=str(identity.tenant_id)
        )

        # Generate JWT token
        from manushya.core.auth import create_identity_token
        token = create_identity_token(identity)

        return InvitationAcceptResponse(
            identity={
                "id": str(identity.id),
                "external_id": identity.external_id,
                "role": identity.role,
                "claims": identity.claims,
                "tenant_id": str(identity.tenant_id) if identity.tenant_id else None,
            },
            token=token
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        ) from e


@router.post("/resend/{invitation_id}")
async def resend_invitation(
    invitation_id: uuid.UUID,
    current_identity: Identity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
):
    """Resend an invitation email."""
    # Check permissions
    policy_engine = PolicyEngine(db)
    await policy_engine.check_identity_access(
        current_identity, "write", target_role="admin"
    )

    stmt = select(Invitation).where(Invitation.id == invitation_id)
    # Tenant filtering
    if current_identity.tenant_id is not None:
        stmt = stmt.where(Invitation.tenant_id == current_identity.tenant_id)
    # else: global/system-level identity can see all

    result = await db.execute(stmt)
    invitation = result.scalar_one_or_none()

    if not invitation:
        raise NotFoundError("Invitation not found")

    if invitation.is_accepted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot resend accepted invitation"
        )

    if invitation.is_expired:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot resend expired invitation"
        )

    # Get tenant name
    stmt = select(Tenant).where(Tenant.id == invitation.tenant_id)
    result = await db.execute(stmt)
    tenant = result.scalar_one_or_none()

    # Generate email content (in a real implementation, this would send the email)
    email_content = InvitationService.generate_invitation_email_content(
        invitation=invitation,
        base_url="http://localhost:8000",  # This should come from settings
        tenant_name=tenant.name if tenant else "Unknown"
    )

    # Create audit log
    audit_log = AuditLog(
        event_type="invitation.resent",
        actor_id=current_identity.id,
        tenant_id=current_identity.tenant_id,
        meta_data={
            "invitation_id": str(invitation_id),
            "email": invitation.email,
            "email_subject": email_content["subject"],
        },
    )
    db.add(audit_log)
    await db.commit()

    return {
        "message": "Invitation email content generated",
        "email_content": email_content,
        "note": "In production, this would send the actual email"
    }
