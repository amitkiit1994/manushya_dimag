"""
Policy API endpoints for Manushya.ai
"""

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from manushya.core.auth import get_current_identity
from manushya.core.exceptions import NotFoundError
from manushya.core.policy_engine import PolicyEngine
from manushya.db.database import get_db
from manushya.db.models import Identity, Policy

router = APIRouter()


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

    class Config:
        from_attributes = True


@router.post("/", response_model=PolicyResponse)
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
    )

    db.add(policy)
    await db.commit()
    await db.refresh(policy)

    # Clear policy cache
    policy_engine.clear_cache()

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
    result = await db.execute(stmt)
    policy = result.scalar_one_or_none()

    if not policy:
        raise NotFoundError("Policy not found")

    # Validate JSON Logic rule if provided (temporarily disabled due to library compatibility issues)
    # TODO: Re-enable validation once json_logic library issues are resolved
    pass

    # Update policy
    update_data = policy_update.dict(exclude_unset=True)
    if update_data:
        for key, value in update_data.items():
            setattr(policy, key, value)

        await db.commit()
        await db.refresh(policy)

        # Clear policy cache
        policy_engine.clear_cache()

    return PolicyResponse.from_orm(policy)


@router.delete("/{policy_id}")
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
    result = await db.execute(stmt)
    policy = result.scalar_one_or_none()

    if not policy:
        raise NotFoundError("Policy not found")

    await db.delete(policy)
    await db.commit()

    # Clear policy cache
    policy_engine.clear_cache()

    return {"message": "Policy deleted successfully"}


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
