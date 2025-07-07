"""
API Key management endpoints for Manushya.ai
"""

import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from manushya.core.api_key_auth import ApiKeyAuth, require_api_key_auth
from manushya.core.auth import get_current_identity
from manushya.core.exceptions import NotFoundError
from manushya.core.policy_engine import PolicyEngine
from manushya.db.database import get_db
from manushya.db.models import ApiKey, AuditLog, Identity
from manushya.services.webhook_service import WebhookService

router = APIRouter()


# Pydantic models
class ApiKeyCreate(BaseModel):
    name: str = Field(..., description="Name for the API key")
    scopes: list[str] = Field(default_factory=list, description="List of scopes for the API key")
    expires_in_days: int | None = Field(None, description="Expiration in days (optional)")


class ApiKeyUpdate(BaseModel):
    name: str | None = Field(None, description="Name for the API key")
    scopes: list[str] | None = Field(None, description="List of scopes for the API key")
    is_active: bool | None = Field(None, description="Whether the API key is active")
    expires_in_days: int | None = Field(None, description="Expiration in days (optional)")


class ApiKeyResponse(BaseModel):
    id: uuid.UUID
    name: str
    scopes: list[str]
    is_active: bool
    expires_at: datetime | None
    last_used_at: datetime | None
    created_at: datetime
    updated_at: datetime
    tenant_id: uuid.UUID | None = None

    class Config:
        from_attributes = True


class ApiKeyCreateResponse(BaseModel):
    api_key: ApiKeyResponse
    secret_key: str = Field(..., description="The actual API key (only shown once)")


@router.post("/", response_model=ApiKeyCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    api_key_data: ApiKeyCreate,
    db: AsyncSession = Depends(get_db),
    current_identity: Identity = Depends(get_current_identity)
):
    """Create a new API key."""
    try:
        # Auto-fill tenant_id from current identity
        tenant_id = current_identity.tenant_id
        if not tenant_id:
            raise HTTPException(status_code=400, detail="Identity must belong to a tenant")

        # Generate API key
        api_key_value = ApiKeyAuth.generate_api_key()
        key_hash = ApiKeyAuth.hash_api_key(api_key_value)

        api_key = ApiKey(
            name=api_key_data.name,
            key_hash=key_hash,
            identity_id=current_identity.id,
            scopes=api_key_data.scopes,
            is_active=True,
            expires_at=datetime.utcnow() + timedelta(days=api_key_data.expires_in_days) if api_key_data.expires_in_days else None,
            tenant_id=tenant_id
        )

        db.add(api_key)
        await db.commit()
        await db.refresh(api_key)

        # Trigger webhook for API key creation
        await WebhookService.trigger_webhook(
            db=db,
            event_type="api_key.created",
            payload={
                "id": str(api_key.id),
                "name": api_key.name,
                "identity_id": str(api_key.identity_id),
                "tenant_id": str(api_key.tenant_id),
                "created_at": api_key.created_at.isoformat()
            },
            tenant_id=str(tenant_id)
        )

        return ApiKeyCreateResponse(
            api_key=ApiKeyResponse.from_orm(api_key),
            secret_key=api_key_value
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create API key: {str(e)}") from e


@router.get("/{api_key_id}", response_model=ApiKeyResponse)
async def get_api_key(
    api_key_id: uuid.UUID,
    current_identity: Identity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
):
    """Get API key by ID."""
    # Check permissions
    policy_engine = PolicyEngine(db)
    await policy_engine.check_identity_access(
        current_identity, "read", target_role="admin"
    )

    stmt = select(ApiKey).where(ApiKey.id == api_key_id)
    # Tenant filtering
    if current_identity.tenant_id is not None:
        stmt = stmt.where(ApiKey.tenant_id == current_identity.tenant_id)
    # else: global/system-level identity can see all

    result = await db.execute(stmt)
    api_key = result.scalar_one_or_none()

    if not api_key:
        raise NotFoundError("API key not found")

    return ApiKeyResponse.from_orm(api_key)


@router.get("/", response_model=list[ApiKeyResponse])
async def list_api_keys(
    is_active: bool | None = None,
    current_identity: Identity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
):
    """List API keys."""
    # Check permissions
    policy_engine = PolicyEngine(db)
    await policy_engine.check_identity_access(
        current_identity, "read", target_role="admin"
    )

    stmt = select(ApiKey)

    if is_active is not None:
        stmt = stmt.where(ApiKey.is_active == is_active)

    # Tenant filtering
    if current_identity.tenant_id is not None:
        stmt = stmt.where(ApiKey.tenant_id == current_identity.tenant_id)
    # else: global/system-level identity can see all

    stmt = stmt.order_by(ApiKey.created_at.desc())
    result = await db.execute(stmt)
    api_keys = result.scalars().all()

    return [ApiKeyResponse.from_orm(api_key) for api_key in api_keys]


@router.put("/{api_key_id}", response_model=ApiKeyResponse)
async def update_api_key(
    api_key_id: uuid.UUID,
    api_key_update: ApiKeyUpdate,
    current_identity: Identity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
):
    """Update API key."""
    # Check permissions
    policy_engine = PolicyEngine(db)
    await policy_engine.check_identity_access(
        current_identity, "write", target_role="admin"
    )

    stmt = select(ApiKey).where(ApiKey.id == api_key_id)
    # Tenant filtering
    if current_identity.tenant_id is not None:
        stmt = stmt.where(ApiKey.tenant_id == current_identity.tenant_id)
    # else: global/system-level identity can see all

    result = await db.execute(stmt)
    api_key = result.scalar_one_or_none()

    if not api_key:
        raise NotFoundError("API key not found")

    # Store before state for audit
    before_state = {
        "name": api_key.name,
        "scopes": api_key.scopes,
        "is_active": api_key.is_active,
        "expires_at": api_key.expires_at.isoformat() if api_key.expires_at else None,
    }

    # Update API key
    update_data = api_key_update.dict(exclude_unset=True)
    if update_data:
        for key, value in update_data.items():
            if key == "expires_in_days":
                if value is not None:
                    api_key.expires_at = datetime.utcnow() + timedelta(days=value)
                else:
                    api_key.expires_at = None
            else:
                setattr(api_key, key, value)

        await db.commit()
        await db.refresh(api_key)

        # Create audit log
        audit_log = AuditLog(
            event_type="api_key.updated",
            actor_id=current_identity.id,
            tenant_id=current_identity.tenant_id,
            before_state=before_state,
            after_state={
                "name": api_key.name,
                "scopes": api_key.scopes,
                "is_active": api_key.is_active,
                "expires_at": api_key.expires_at.isoformat() if api_key.expires_at else None,
            },
        )
        db.add(audit_log)
        await db.commit()

    return ApiKeyResponse.from_orm(api_key)


@router.delete("/{api_key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    api_key_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_identity: Identity = Depends(get_current_identity)
):
    """Revoke an API key."""
    # Get API key
    stmt = select(ApiKey).where(ApiKey.id == api_key_id)
    result = await db.execute(stmt)
    api_key = result.scalar_one_or_none()

    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")

    # Check tenant access
    if current_identity.tenant_id and api_key.tenant_id != current_identity.tenant_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Check if user owns the API key or is admin
    if api_key.identity_id != current_identity.id and current_identity.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    # Store API key data for webhook before revocation
    api_key_data = {
        "id": str(api_key.id),
        "name": api_key.name,
        "identity_id": str(api_key.identity_id),
        "tenant_id": str(api_key.tenant_id),
        "revoked_at": datetime.utcnow().isoformat()
    }

    # Revoke API key
    api_key.is_active = False
    api_key.updated_at = datetime.utcnow()
    await db.commit()

    # Trigger webhook for API key revocation
    await WebhookService.trigger_webhook(
        db=db,
        event_type="api_key.revoked",
        payload=api_key_data,
        tenant_id=str(api_key.tenant_id)
    )

    return None


@router.post("/test")
async def test_api_key_auth(
    current_identity: Identity = Depends(require_api_key_auth),
):
    """Test API key authentication."""
    return {
        "message": "API key authentication successful",
        "identity": {
            "id": str(current_identity.id),
            "external_id": current_identity.external_id,
            "role": current_identity.role,
            "tenant_id": str(current_identity.tenant_id) if current_identity.tenant_id else None,
        }
    }
