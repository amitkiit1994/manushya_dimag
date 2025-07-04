"""
Identity API endpoints for Manushya.ai
"""

import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from manushya.db.database import get_db
from manushya.db.models import Identity
from manushya.core.auth import get_current_identity, create_identity_token
from manushya.core.policy_engine import PolicyEngine
from manushya.core.exceptions import NotFoundError, ConflictError, AuthorizationError

router = APIRouter()


# Pydantic models
class IdentityCreate(BaseModel):
    external_id: str = Field(..., description="External identifier for the identity")
    role: str = Field(..., description="Role of the identity")
    claims: Dict[str, Any] = Field(default_factory=dict, description="Additional claims")


class IdentityUpdate(BaseModel):
    role: Optional[str] = Field(None, description="Role of the identity")
    claims: Optional[Dict[str, Any]] = Field(None, description="Additional claims")
    is_active: Optional[bool] = Field(None, description="Whether the identity is active")


class IdentityResponse(BaseModel):
    id: uuid.UUID
    external_id: str
    role: str
    claims: Dict[str, Any]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class IdentityTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    identity: IdentityResponse


@router.post("/", response_model=IdentityTokenResponse)
async def create_identity(
    identity_data: IdentityCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new identity and return access token."""
    try:
        # Check if identity already exists
        stmt = select(Identity).where(Identity.external_id == identity_data.external_id)
        result = await db.execute(stmt)
        existing_identity = result.scalar_one_or_none()
        
        if existing_identity:
            # Update existing identity
            existing_identity.role = identity_data.role
            existing_identity.claims = identity_data.claims
            await db.commit()
            await db.refresh(existing_identity)
            identity = existing_identity
        else:
            # Create new identity
            identity = Identity(
                external_id=identity_data.external_id,
                role=identity_data.role,
                claims=identity_data.claims
            )
            db.add(identity)
            await db.commit()
            await db.refresh(identity)
        
        # Create access token
        access_token = create_identity_token(identity)
        
        return IdentityTokenResponse(
            access_token=access_token,
            identity=IdentityResponse.from_orm(identity)
        )
        
    except IntegrityError:
        await db.rollback()
        raise ConflictError("Identity with this external_id already exists")


@router.get("/me", response_model=IdentityResponse)
async def get_current_identity_info(
    current_identity: Identity = Depends(get_current_identity)
):
    """Get current identity information."""
    return IdentityResponse.from_orm(current_identity)


@router.put("/me", response_model=IdentityResponse)
async def update_current_identity(
    identity_update: IdentityUpdate,
    current_identity: Identity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db)
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
    
    return IdentityResponse.from_orm(current_identity)


@router.get("/{identity_id}", response_model=IdentityResponse)
async def get_identity(
    identity_id: uuid.UUID,
    current_identity: Identity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db)
):
    """Get identity by ID (requires appropriate permissions)."""
    # Check permissions
    policy_engine = PolicyEngine(db)
    await policy_engine.check_identity_access(
        current_identity, 
        "read", 
        target_role=None
    )
    
    stmt = select(Identity).where(Identity.id == identity_id)
    result = await db.execute(stmt)
    identity = result.scalar_one_or_none()
    
    if not identity:
        raise NotFoundError("Identity not found")
    
    return IdentityResponse.from_orm(identity)


@router.get("/", response_model=List[IdentityResponse])
async def list_identities(
    skip: int = 0,
    limit: int = 100,
    role: Optional[str] = None,
    current_identity: Identity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db)
):
    """List identities (requires appropriate permissions)."""
    # Check permissions
    policy_engine = PolicyEngine(db)
    await policy_engine.check_identity_access(
        current_identity, 
        "list", 
        target_role=None
    )
    
    stmt = select(Identity)
    
    if role:
        stmt = stmt.where(Identity.role == role)
    
    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    identities = result.scalars().all()
    
    return [IdentityResponse.from_orm(identity) for identity in identities]


@router.delete("/{identity_id}")
async def delete_identity(
    identity_id: uuid.UUID,
    current_identity: Identity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db)
):
    """Delete identity (requires appropriate permissions)."""
    # Check permissions
    policy_engine = PolicyEngine(db)
    await policy_engine.check_identity_access(
        current_identity, 
        "delete", 
        target_role=None
    )
    
    stmt = select(Identity).where(Identity.id == identity_id)
    result = await db.execute(stmt)
    identity = result.scalar_one_or_none()
    
    if not identity:
        raise NotFoundError("Identity not found")
    
    # Soft delete
    identity.is_active = False
    await db.commit()
    
    return {"message": "Identity deleted successfully"} 