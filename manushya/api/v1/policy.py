"""
Policy API endpoints for Manushya.ai
"""

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from manushya.core.auth import get_current_identity
from manushya.core.exceptions import NotFoundError
from manushya.core.policy_engine import PolicyEngine
from manushya.core.rate_limiter import RateLimiter
from manushya.db.database import get_db
from manushya.db.models import AuditLog, Identity, Policy, RateLimit
from manushya.services.webhook_service import WebhookService

router = APIRouter()
admin_router = APIRouter(prefix="/v1/admin", tags=["admin"])
monitoring_router = APIRouter(prefix="/v1/monitoring", tags=["monitoring"])


# Pydantic models
class PolicyCreate(BaseModel):
    role: str = Field(..., description="Role this policy applies to")
    rule: dict[str, Any] = Field(..., description="JSON Logic rule")
    description: str | None = Field(None, description="Policy description")
    priority: int = Field(
        default=0, description="Policy priority (higher = more important)"
    )
    is_active: bool = Field(default=True, description="Whether the policy is active")


class PolicyUpdate(BaseModel):
    rule: dict[str, Any] | None = Field(None, description="JSON Logic rule")
    description: str | None = Field(None, description="Policy description")
    priority: int | None = Field(None, description="Policy priority")
    is_active: bool | None = Field(None, description="Whether the policy is active")


class PolicyResponse(BaseModel):
    id: uuid.UUID
    role: str
    rule: dict[str, Any]
    description: str | None
    priority: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    tenant_id: uuid.UUID | None = None

    class Config:
        from_attributes = True


class BulkDeletePolicyRequest(BaseModel):
    policy_ids: list[uuid.UUID] = Field(..., description="List of policy IDs to delete")
    reason: str | None = Field(None, description="Reason for bulk deletion")


class BulkDeletePolicyResponse(BaseModel):
    deleted_count: int
    failed_count: int
    failed_policies: list[dict[str, Any]]
    message: str


@router.post("/", response_model=PolicyResponse, status_code=status.HTTP_201_CREATED)
async def create_policy(
    policy_data: PolicyCreate,
    current_identity: Identity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
):
    """Create a new policy."""
    # Check permissions - only admins can create policies
    policy_engine = PolicyEngine(db)
    await policy_engine.check_identity_access(
        current_identity, "write", target_role="admin"
    )

    # Validate JSON Logic rule (temporarily disabled due to library compatibility issues)
    # TODO: Re-enable validation once json_logic library issues are resolved
    pass

    policy = Policy(
        role=policy_data.role,
        rule=policy_data.rule,
        description=policy_data.description,
        priority=policy_data.priority,
        is_active=policy_data.is_active,
        tenant_id=current_identity.tenant_id,
    )

    db.add(policy)
    await db.commit()
    await db.refresh(policy)

    # Create audit log
    audit_log = AuditLog(
        event_type="policy.created",
        actor_id=current_identity.id,
        tenant_id=current_identity.tenant_id,
        after_state={
            "role": policy.role,
            "rule": policy.rule,
            "description": policy.description,
            "priority": policy.priority,
            "is_active": policy.is_active,
        },
    )
    db.add(audit_log)
    await db.commit()

    # Clear policy cache
    policy_engine.clear_cache()

    # Trigger webhook for policy creation
    await WebhookService.trigger_webhook(
        db=db,
        event_type="policy.created",
        payload={
            "id": str(policy.id),
            "role": policy.role,
            "description": policy.description,
            "priority": policy.priority,
            "is_active": policy.is_active,
            "tenant_id": str(policy.tenant_id),
            "created_at": policy.created_at.isoformat()
        },
        tenant_id=str(policy.tenant_id)
    )

    return PolicyResponse.from_orm(policy)


@router.get("/{policy_id}", response_model=PolicyResponse)
async def get_policy(
    policy_id: uuid.UUID,
    current_identity: Identity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
):
    """Get policy by ID."""
    # Check permissions
    policy_engine = PolicyEngine(db)
    await policy_engine.check_identity_access(
        current_identity, "read", target_role="admin"
    )

    stmt = select(Policy).where(Policy.id == policy_id)
    # Tenant filtering
    if current_identity.tenant_id is not None:
        stmt = stmt.where(Policy.tenant_id == current_identity.tenant_id)
    # else: global/system-level identity can see all

    result = await db.execute(stmt)
    policy = result.scalar_one_or_none()

    if not policy:
        raise NotFoundError("Policy not found")

    return PolicyResponse.from_orm(policy)


@router.get("/", response_model=list[PolicyResponse])
async def list_policies(
    role: str | None = None,
    is_active: bool | None = None,
    current_identity: Identity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
):
    """List policies."""
    # Check permissions
    policy_engine = PolicyEngine(db)
    await policy_engine.check_identity_access(
        current_identity, "read", target_role="admin"
    )

    stmt = select(Policy)

    if role:
        stmt = stmt.where(Policy.role == role)

    if is_active is not None:
        stmt = stmt.where(Policy.is_active == is_active)

    # Tenant filtering
    if current_identity.tenant_id is not None:
        stmt = stmt.where(Policy.tenant_id == current_identity.tenant_id)
    # else: global/system-level identity can see all

    stmt = stmt.order_by(Policy.role, Policy.priority.desc())
    result = await db.execute(stmt)
    policies = result.scalars().all()

    return [PolicyResponse.from_orm(policy) for policy in policies]


@router.put("/{policy_id}", response_model=PolicyResponse)
async def update_policy(
    policy_id: uuid.UUID,
    policy_update: PolicyUpdate,
    current_identity: Identity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
):
    """Update policy."""
    # Check permissions
    policy_engine = PolicyEngine(db)
    await policy_engine.check_identity_access(
        current_identity, "write", target_role="admin"
    )

    stmt = select(Policy).where(Policy.id == policy_id)
    # Tenant filtering
    if current_identity.tenant_id is not None:
        stmt = stmt.where(Policy.tenant_id == current_identity.tenant_id)
    # else: global/system-level identity can see all

    result = await db.execute(stmt)
    policy = result.scalar_one_or_none()

    if not policy:
        raise NotFoundError("Policy not found")

    # Validate JSON Logic rule if provided (temporarily disabled due to library compatibility issues)
    # TODO: Re-enable validation once json_logic library issues are resolved
    pass

    # Store before state for audit
    before_state = {
        "role": policy.role,
        "rule": policy.rule,
        "description": policy.description,
        "priority": policy.priority,
        "is_active": policy.is_active,
    }

    # Update policy
    update_data = policy_update.dict(exclude_unset=True)
    if update_data:
        for key, value in update_data.items():
            setattr(policy, key, value)

        await db.commit()
        await db.refresh(policy)

        # Create audit log
        audit_log = AuditLog(
            event_type="policy.updated",
            actor_id=current_identity.id,
            tenant_id=current_identity.tenant_id,
            before_state=before_state,
            after_state={
                "role": policy.role,
                "rule": policy.rule,
                "description": policy.description,
                "priority": policy.priority,
                "is_active": policy.is_active,
            },
        )
        db.add(audit_log)
        await db.commit()

        # Clear policy cache
        policy_engine.clear_cache()

    # Trigger webhook for policy update
    await WebhookService.trigger_webhook(
        db=db,
        event_type="policy.updated",
        payload={
            "id": str(policy.id),
            "role": policy.role,
            "description": policy.description,
            "priority": policy.priority,
            "is_active": policy.is_active,
            "tenant_id": str(policy.tenant_id),
            "updated_at": policy.updated_at.isoformat()
        },
        tenant_id=str(policy.tenant_id)
    )

    return PolicyResponse.from_orm(policy)


@router.delete("/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_policy(
    policy_id: uuid.UUID,
    current_identity: Identity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
):
    """Delete policy."""
    # Check permissions
    policy_engine = PolicyEngine(db)
    await policy_engine.check_identity_access(
        current_identity, "delete", target_role="admin"
    )

    stmt = select(Policy).where(Policy.id == policy_id)
    # Tenant filtering
    if current_identity.tenant_id is not None:
        stmt = stmt.where(Policy.tenant_id == current_identity.tenant_id)
    # else: global/system-level identity can see all

    result = await db.execute(stmt)
    policy = result.scalar_one_or_none()

    if not policy:
        raise NotFoundError("Policy not found")

    # Store before state for audit
    before_state = {
        "role": policy.role,
        "rule": policy.rule,
        "description": policy.description,
        "priority": policy.priority,
        "is_active": policy.is_active,
    }

    await db.delete(policy)
    await db.commit()

    # Create audit log
    audit_log = AuditLog(
        event_type="policy.deleted",
        actor_id=current_identity.id,
        tenant_id=current_identity.tenant_id,
        before_state=before_state,
    )
    db.add(audit_log)
    await db.commit()

    # Clear policy cache
    policy_engine.clear_cache()

    # Store policy data for webhook before deletion
    policy_data = {
        "id": str(policy.id),
        "role": policy.role,
        "description": policy.description,
        "priority": policy.priority,
        "is_active": policy.is_active,
        "tenant_id": str(policy.tenant_id),
        "deleted_at": datetime.utcnow().isoformat()
    }

    # Trigger webhook for policy deletion
    await WebhookService.trigger_webhook(
        db=db,
        event_type="policy.deleted",
        payload=policy_data,
        tenant_id=str(policy.tenant_id)
    )

    return None


@router.post("/bulk-delete", response_model=BulkDeletePolicyResponse)
async def bulk_delete_policies(
    delete_request: BulkDeletePolicyRequest,
    current_identity: Identity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
):
    """Bulk delete policies (requires admin permissions)."""
    # Check permissions
    policy_engine = PolicyEngine(db)
    await policy_engine.check_identity_access(
        current_identity, "delete", target_role="admin"
    )

    deleted_count = 0
    failed_count = 0
    failed_policies = []

    for policy_id in delete_request.policy_ids:
        try:
            stmt = select(Policy).where(Policy.id == policy_id)
            # Tenant filtering
            if current_identity.tenant_id is not None:
                stmt = stmt.where(Policy.tenant_id == current_identity.tenant_id)
            # else: global/system-level identity can see all

            result = await db.execute(stmt)
            policy = result.scalar_one_or_none()

            if not policy:
                failed_count += 1
                failed_policies.append({
                    "policy_id": str(policy_id),
                    "error": "Policy not found"
                })
                continue

            # Prevent deletion of critical system policies
            if policy.role in ["admin", "system"] and policy.priority >= 100:
                failed_count += 1
                failed_policies.append({
                    "policy_id": str(policy_id),
                    "role": policy.role,
                    "priority": policy.priority,
                    "error": "Cannot delete critical system policy"
                })
                continue

            await db.delete(policy)
            deleted_count += 1

        except Exception as e:
            failed_count += 1
            failed_policies.append({
                "policy_id": str(policy_id),
                "error": str(e)
            })

    # Commit all changes
    await db.commit()

    # Clear policy cache after bulk deletion
    policy_engine.clear_cache()

    # Create audit log for bulk operation
    audit_log = AuditLog(
        event_type="policy.bulk_deleted",
        actor_id=current_identity.id,
        tenant_id=current_identity.tenant_id,
        meta_data={
            "deleted_count": deleted_count,
            "failed_count": failed_count,
            "reason": delete_request.reason,
            "requested_ids": [str(id) for id in delete_request.policy_ids],
            "failed_policies": failed_policies
        }
    )
    db.add(audit_log)
    await db.commit()

    # Trigger webhook for bulk policy deletion
    await WebhookService.trigger_webhook(
        db=db,
        event_type="policy.bulk_deleted",
        payload={
            "deleted_count": deleted_count,
            "failed_count": failed_count,
            "reason": delete_request.reason,
            "requested_ids": [str(id) for id in delete_request.policy_ids],
            "failed_policies": failed_policies
        },
        tenant_id=str(current_identity.tenant_id)
    )

    return BulkDeletePolicyResponse(
        deleted_count=deleted_count,
        failed_count=failed_count,
        failed_policies=failed_policies,
        message=f"Bulk delete completed: {deleted_count} deleted, {failed_count} failed"
    )


@router.post("/test")
async def test_policy(
    role: str,
    action: str,
    resource: str,
    context: dict[str, Any],
    current_identity: Identity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
):
    """Test a policy evaluation."""
    # Check permissions
    policy_engine = PolicyEngine(db)
    await policy_engine.check_identity_access(
        current_identity, "read", target_role="admin"
    )

    try:
        result = await policy_engine.evaluate_policy(role, action, resource, context)
        return {
            "allowed": result,
            "role": role,
            "action": action,
            "resource": resource,
            "context": context,
        }
    except Exception as e:
        return {
            "allowed": False,
            "error": str(e),
            "role": role,
            "action": action,
            "resource": resource,
            "context": context,
        }

# Admin: List all rate limits
@admin_router.get("/rate-limits", summary="List all rate limit records (admin only)")
async def list_all_rate_limits(
    db: AsyncSession = Depends(get_db),
    identity: Identity = Depends(get_current_identity)
):
    if identity.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    result = await db.execute(RateLimit.__table__.select())
    records = result.fetchall()
    return [dict(r) for r in records]

# Admin: Delete all rate limits
@admin_router.delete("/rate-limits", summary="Delete all rate limit records (admin only)")
async def delete_all_rate_limits(
    db: AsyncSession = Depends(get_db),
    identity: Identity = Depends(get_current_identity)
):
    if identity.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    await db.execute(delete(RateLimit))
    await db.commit()
    return {"message": "All rate limit records deleted"}

# Monitoring: Get current rate limit info for the caller
@monitoring_router.get("/rate-limits", summary="Get current rate limit info for the caller")
async def get_my_rate_limit(
    request: Request,
    db: AsyncSession = Depends(get_db),
    identity: Identity = Depends(get_current_identity)
):
    info = await RateLimiter.get_rate_limit_info(request, db, identity)
    return info

# Monitoring: Get API usage analytics (stub)
@monitoring_router.get("/usage", summary="Get API usage analytics (stub)")
async def get_api_usage_analytics(
    db: AsyncSession = Depends(get_db),
    identity: Identity = Depends(get_current_identity)
):
    # Stub: count total rate limit records and requests
    result = await db.execute(RateLimit.__table__.select())
    records = result.fetchall()
    total_requests = sum(r.request_count for r in records)
    return {
        "total_rate_limit_records": len(records),
        "total_requests_tracked": total_requests,
        "note": "This is a stub. Extend for real analytics."
    }
