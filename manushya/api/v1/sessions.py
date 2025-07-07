"""
Session management endpoints for Manushya.ai
"""

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from manushya.core.auth import get_current_identity, refresh_access_token
from manushya.core.exceptions import NotFoundError
from manushya.core.session_service import SessionService
from manushya.db.database import get_db
from manushya.db.models import AuditLog, Identity, Session
from manushya.services.webhook_service import WebhookService

router = APIRouter()


# Pydantic models
class SessionResponse(BaseModel):
    id: uuid.UUID
    device_info: dict[str, Any]
    ip_address: str | None
    user_agent: str | None
    is_active: bool
    expires_at: datetime
    last_used_at: datetime
    created_at: datetime
    updated_at: datetime
    tenant_id: uuid.UUID | None = None

    class Config:
        from_attributes = True


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="Refresh token")


class RefreshTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int


class RevokeSessionRequest(BaseModel):
    session_id: uuid.UUID = Field(..., description="Session ID to revoke")


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(
    refresh_request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """Refresh access token using refresh token."""
    tokens = await refresh_access_token(refresh_request.refresh_token, db)

    if not tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )

    return RefreshTokenResponse(
        access_token=str(tokens["access_token"]),
        refresh_token=str(tokens["refresh_token"]),
        token_type=str(tokens["token_type"]),
        expires_in=int(tokens["expires_in"])
    )


@router.get("/", response_model=list[SessionResponse])
async def list_sessions(
    current_identity: Identity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
):
    """List all active sessions for the current identity."""
    sessions = await SessionService.get_active_sessions_for_identity(
        db=db,
        identity_id=str(current_identity.id)
    )

    return [SessionResponse.from_orm(session) for session in sessions]


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: uuid.UUID,
    current_identity: Identity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
):
    """Get specific session details."""
    stmt = select(Session).where(
        Session.id == session_id,
        Session.identity_id == current_identity.id
    )
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()

    if not session:
        raise NotFoundError("Session not found")

    return SessionResponse.from_orm(session)


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_session(
    session_id: uuid.UUID,
    current_identity: Identity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
):
    """Revoke a specific session."""
    # Verify session belongs to current identity
    stmt = select(Session).where(
        Session.id == session_id,
        Session.identity_id == current_identity.id
    )
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()

    if not session:
        raise NotFoundError("Session not found")

    # Store before state for audit
    before_state = {
        "session_id": str(session.id),
        "device_info": session.device_info,
        "ip_address": session.ip_address,
        "user_agent": session.user_agent,
        "is_active": session.is_active,
        "expires_at": session.expires_at.isoformat(),
    }

    # Store session data for webhook before revocation
    session_data = {
        "id": str(session.id),
        "identity_id": str(session.identity_id),
        "device_info": session.device_info,
        "ip_address": session.ip_address,
        "user_agent": session.user_agent,
        "tenant_id": str(session.tenant_id),
        "revoked_at": datetime.utcnow().isoformat()
    }

    # Revoke session
    success = await SessionService.revoke_session(db, str(session_id))

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke session"
        )

    # Create audit log
    audit_log = AuditLog(
        event_type="session.revoked",
        actor_id=current_identity.id,
        tenant_id=current_identity.tenant_id,
        before_state=before_state,
    )
    db.add(audit_log)
    await db.commit()

    # Trigger webhook for session revocation
    await WebhookService.trigger_webhook(
        db=db,
        event_type="session.revoked",
        payload=session_data,
        tenant_id=str(session.tenant_id)
    )

    return {"message": "Session revoked successfully"}


@router.delete("/")
async def revoke_all_sessions(
    current_identity: Identity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
):
    """Revoke all sessions for the current identity."""
    revoked_count = await SessionService.revoke_all_sessions_for_identity(
        db=db,
        identity_id=str(current_identity.id)
    )

    # Create audit log
    audit_log = AuditLog(
        event_type="sessions.revoked_all",
        actor_id=current_identity.id,
        tenant_id=current_identity.tenant_id,
        meta_data={
            "revoked_count": revoked_count,
        },
    )
    db.add(audit_log)
    await db.commit()

    return {
        "message": f"Revoked {revoked_count} sessions",
        "revoked_count": revoked_count
    }


@router.post("/cleanup")
async def cleanup_expired_sessions(
    current_identity: Identity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
):
    """Clean up expired sessions (admin only)."""
    # Check permissions - only admins can cleanup sessions
    from manushya.core.policy_engine import PolicyEngine
    policy_engine = PolicyEngine(db)
    await policy_engine.check_identity_access(
        current_identity, "write", target_role="admin"
    )

    cleaned_count = await SessionService.cleanup_expired_sessions(db)

    # Create audit log
    audit_log = AuditLog(
        event_type="sessions.cleanup",
        actor_id=current_identity.id,
        tenant_id=current_identity.tenant_id,
        meta_data={
            "cleaned_count": cleaned_count,
        },
    )
    db.add(audit_log)
    await db.commit()

    return {
        "message": f"Cleaned up {cleaned_count} expired sessions",
        "cleaned_count": cleaned_count
    }


@router.post("/test")
async def test_session_auth(
    current_identity: Identity = Depends(get_current_identity),
):
    """Test session authentication."""
    return {
        "message": "Session authentication successful",
        "identity": {
            "id": str(current_identity.id),
            "external_id": current_identity.external_id,
            "role": current_identity.role,
            "tenant_id": str(current_identity.tenant_id) if current_identity.tenant_id else None,
        }
    }
