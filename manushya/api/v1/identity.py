"""
Identity API endpoints for Manushya.ai
"""

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query
from jose import jwt
from pydantic import BaseModel, Field
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request as StarletteRequest

from manushya.core.auth import (
    create_identity_token,
    get_current_identity,
)
from manushya.core.exceptions import ConflictError, NotFoundError
from manushya.core.policy_engine import PolicyEngine
from manushya.core.session_service import SessionService
from manushya.db.database import get_db
from manushya.db.models import Identity, Tenant
from manushya.services.webhook_service import WebhookService

router = APIRouter()


# Pydantic models
class IdentityCreate(BaseModel):
    external_id: str = Field(..., description="External identifier for the identity")
    role: str = Field(..., description="Role of the identity")
    claims: dict[str, Any] = Field(
        default_factory=dict, description="Additional claims"
    )


class IdentityUpdate(BaseModel):
    role: str | None = Field(None, description="Role of the identity")
    claims: dict[str, Any] | None = Field(None, description="Additional claims")
    is_active: bool | None = Field(None, description="Whether the identity is active")


class IdentityResponse(BaseModel):
    id: uuid.UUID
    external_id: str
    role: str
    claims: dict[str, Any]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    tenant_id: uuid.UUID | None = None

    class Config:
        from_attributes = True


class IdentityTokenResponse(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"
    identity: IdentityResponse


class BulkDeleteRequest(BaseModel):
    identity_ids: list[uuid.UUID] = Field(
        ..., description="List of identity IDs to delete"
    )
    hard_delete: bool = Field(
        default=False, description="Perform hard delete instead of soft delete"
    )
    reason: str | None = Field(None, description="Reason for bulk deletion")


class BulkDeleteResponse(BaseModel):
    deleted_count: int
    failed_count: int
    failed_identities: list[dict[str, Any]]
    message: str


@router.post("/", response_model=IdentityTokenResponse)
async def create_identity(
    identity_data: IdentityCreate,
    http_request: StarletteRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create a new identity and return access token.
    Injects tenant_id for multi-tenancy."""
    try:
        # Initialize tenant_id
        tenant_id = None
        # Try to extract tenant_id from JWT context (if available)
        if http_request is not None:
            auth_header = http_request.headers.get("authorization")
            if auth_header and auth_header.lower().startswith("bearer "):
                token = auth_header.split(" ", 1)[1]
                try:
                    # Use the same secret as your JWT config
                    claims = jwt.get_unverified_claims(token)
                    tenant_id = claims.get("tenant_id")
                except Exception:
                    pass
        # If no tenant_id, create a new tenant (first user in a workspace)
        if not tenant_id:
            new_tenant = Tenant(name=f"Tenant for {identity_data.external_id}")
            db.add(new_tenant)
            await db.commit()
            await db.refresh(new_tenant)
            tenant_id = new_tenant.id
            # --- BOOTSTRAP POLICY: Grant admin full access for this tenant ---
            from manushya.db.models import Policy
            admin_policy = Policy(
                role="admin",
                rule={"actions": ["*"], "resource": "*", "effect": "allow"},
                description="Default admin policy for new tenant (bootstrap)",
                is_active=True,
                priority=100,
                tenant_id=tenant_id,
            )
            db.add(admin_policy)
            await db.commit()
            await db.refresh(admin_policy)
            # --------------------------------------------------------------
        # Check if identity already exists
        stmt = select(Identity).where(Identity.external_id == identity_data.external_id)
        result = await db.execute(stmt)
        existing_identity = result.scalar_one_or_none()
        if existing_identity:
            # Update existing identity
            existing_identity.role = identity_data.role
            existing_identity.claims = identity_data.claims
            existing_identity.tenant_id = tenant_id
            await db.commit()
            await db.refresh(existing_identity)
            identity = existing_identity
        else:
            # Create new identity
            identity = Identity(
                external_id=identity_data.external_id,
                role=identity_data.role,
                claims=identity_data.claims,
                tenant_id=tenant_id,
            )
            db.add(identity)
            await db.commit()
            await db.refresh(identity)
        # Create access token
        access_token = create_identity_token(identity)
        # Create session and refresh token
        session, refresh_token = await SessionService.create_session(
            db=db, identity=identity, request=http_request, expires_in_days=30
        )
        # Trigger webhook for identity creation
        await WebhookService.trigger_webhook(
            db=db,
            event_type="identity.created",
            payload={
                "id": str(identity.id),
                "external_id": identity.external_id,
                "role": identity.role,
                "tenant_id": str(identity.tenant_id),
                "created_at": identity.created_at.isoformat(),
            },
            tenant_id=str(tenant_id),
        )
        return IdentityTokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            identity=IdentityResponse.from_orm(identity),
        )
    except IntegrityError:
        await db.rollback()
        raise ConflictError("Identity with this external_id already exists") from None


@router.get("/me", response_model=IdentityResponse)
async def get_current_identity_info(
    current_identity: Identity = Depends(get_current_identity),
):
    """Get current identity information."""
    return IdentityResponse.from_orm(current_identity)


@router.put("/me", response_model=IdentityResponse)
async def update_current_identity(
    identity_update: IdentityUpdate,
    current_identity: Identity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
):
    """Update current identity."""
    update_data = identity_update.dict(exclude_unset=True)
    if update_data:
        stmt = (
            update(Identity)
            .where(Identity.id == current_identity.id)
            .values(**update_data)
        )
        await db.execute(stmt)
        await db.commit()
        await db.refresh(current_identity)
    # Trigger webhook for identity update
    await WebhookService.trigger_webhook(
        db=db,
        event_type="identity.updated",
        payload={
            "id": str(current_identity.id),
            "external_id": current_identity.external_id,
            "role": current_identity.role,
            "is_active": current_identity.is_active,
            "tenant_id": str(current_identity.tenant_id),
            "updated_at": current_identity.updated_at.isoformat(),
        },
        tenant_id=str(current_identity.tenant_id),
    )
    return IdentityResponse.from_orm(current_identity)


@router.get("/{identity_id}", response_model=IdentityResponse)
async def get_identity(
    identity_id: uuid.UUID,
    current_identity: Identity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
):
    """Get identity by ID (requires appropriate permissions).
    Only for current tenant unless global/system-level."""
    # Check permissions
    policy_engine = PolicyEngine(db)
    await policy_engine.check_identity_access(
        current_identity, "read", target_identity_id=None
    )
    stmt = select(Identity).where(Identity.id == identity_id)
    # Tenant filtering
    if current_identity.tenant_id is not None:
        stmt = stmt.where(Identity.tenant_id == current_identity.tenant_id)
    # else: global/system-level identity can see all
    result = await db.execute(stmt)
    identity = result.scalar_one_or_none()
    if not identity:
        raise NotFoundError("Identity not found")
    return IdentityResponse.from_orm(identity)


@router.get("/", response_model=list[IdentityResponse])
async def list_identities(
    skip: int = 0,
    limit: int = 100,
    role: str | None = None,
    is_active: bool | None = Query(
        None, description="Filter by active/inactive identities. Default: only active."
    ),
    current_identity: Identity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
):
    """List identities (requires appropriate permissions).
    By default, only active identities are returned.
    Use is_active=false to list inactive, or is_active=all to list all (admin only).
    Only returns identities for the current tenant,
    unless current identity is global/system-level.
    """
    # Check permissions
    policy_engine = PolicyEngine(db)
    await policy_engine.check_identity_access(
        current_identity, "list", target_identity_id=None
    )
    stmt = select(Identity)
    if role:
        stmt = stmt.where(Identity.role == role)
    # Only show active identities by default
    if is_active is None:
        stmt = stmt.where(Identity.is_active)
    else:
        stmt = stmt.where(Identity.is_active == is_active)
    # Tenant filtering
    if current_identity.tenant_id is not None:
        stmt = stmt.where(Identity.tenant_id == current_identity.tenant_id)
    # else: global/system-level identity can see all
    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    identities = result.scalars().all()
    return [IdentityResponse.from_orm(identity) for identity in identities]


@router.delete("/{identity_id}")
async def delete_identity(
    identity_id: uuid.UUID,
    current_identity: Identity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
):
    """Delete identity (requires appropriate permissions)."""
    # Check permissions
    policy_engine = PolicyEngine(db)
    await policy_engine.check_identity_access(
        current_identity, "delete", target_identity_id=None
    )
    stmt = select(Identity).where(Identity.id == identity_id)
    result = await db.execute(stmt)
    identity = result.scalar_one_or_none()
    if not identity:
        raise NotFoundError("Identity not found")
    # Soft delete
    identity.is_active = False
    await db.commit()
    # Trigger webhook for identity deletion
    await WebhookService.trigger_webhook(
        db=db,
        event_type="identity.deleted",
        payload={
            "id": str(identity.id),
            "external_id": identity.external_id,
            "role": identity.role,
            "tenant_id": str(identity.tenant_id),
            "deleted_at": identity.updated_at.isoformat(),
        },
        tenant_id=str(identity.tenant_id),
    )
    return {"message": "Identity deleted successfully"}


@router.post("/bulk-delete", response_model=BulkDeleteResponse)
async def bulk_delete_identities(
    delete_request: BulkDeleteRequest,
    current_identity: Identity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
):
    """Bulk delete identities (requires appropriate permissions)."""
    # Check permissions
    policy_engine = PolicyEngine(db)
    await policy_engine.check_identity_access(
        current_identity, "delete", target_identity_id=None
    )
    deleted_count = 0
    failed_count = 0
    failed_identities = []
    for identity_id in delete_request.identity_ids:
        try:
            stmt = select(Identity).where(Identity.id == identity_id)
            result = await db.execute(stmt)
            identity = result.scalar_one_or_none()
            if not identity:
                failed_count += 1
                failed_identities.append(
                    {
                        "identity_id": str(identity_id),
                        "error": "Identity not found"
                    }
                )
                continue
            # Prevent self-deletion
            if identity.id == current_identity.id:
                failed_count += 1
                failed_identities.append(
                    {
                        "identity_id": str(identity_id),
                        "external_id": identity.external_id,
                        "error": "Cannot delete own identity",
                    }
                )
                continue
            if delete_request.hard_delete:
                # Hard delete - remove from database
                # First check if there are related memories and handle them
                from manushya.db.models import Memory

                memory_stmt = select(Memory).where(Memory.identity_id == identity.id)
                memory_result = await db.execute(memory_stmt)
                related_memories = memory_result.scalars().all()
                if related_memories:
                    # Delete related memories first to avoid foreign key constraint
                    # issues
                    for memory in related_memories:
                        await db.delete(memory)
                # Now delete the identity
                await db.delete(identity)
            else:
                # Soft delete - mark as inactive
                identity.is_active = False
            deleted_count += 1
        except Exception as e:
            failed_count += 1
            failed_identities.append(
                {
                    "identity_id": str(identity_id),
                    "error": str(e),
                }
            )
    # Commit all changes
    await db.commit()
    # Create audit log for bulk operation
    from manushya.db.models import AuditLog

    audit_log = AuditLog(
        event_type="identity.bulk_deleted",
        actor_id=current_identity.id,
        meta_data={
            "deleted_count": deleted_count,
            "failed_count": failed_count,
            "hard_delete": delete_request.hard_delete,
            "reason": delete_request.reason,
            "requested_ids": [str(id) for id in delete_request.identity_ids],
            "failed_identities": failed_identities,
        },
    )
    db.add(audit_log)
    await db.commit()
    # Trigger webhook for bulk deletion
    await WebhookService.trigger_webhook(
        db=db,
        event_type="identity.bulk_deleted",
        payload={
            "deleted_count": deleted_count,
            "failed_count": failed_count,
            "hard_delete": delete_request.hard_delete,
            "reason": delete_request.reason,
            "failed_identities": failed_identities,
        },
        tenant_id=str(current_identity.tenant_id),
    )
    return BulkDeleteResponse(
        deleted_count=deleted_count,
        failed_count=failed_count,
        failed_identities=failed_identities,
        message=(
            f"Bulk delete completed: {deleted_count} deleted, {failed_count} failed"
        ),
    )
