"""
Memory API endpoints for Manushya.ai
"""

import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.dialects.postgresql import array
import numpy as np

from manushya.db.database import get_db
from manushya.db.models import Memory, Identity, AuditLog
from manushya.core.auth import get_current_identity
from manushya.core.policy_engine import PolicyEngine
from manushya.core.exceptions import NotFoundError, ValidationError
from manushya.services.embedding_service import generate_embedding
from manushya.tasks.memory_tasks import create_memory_embedding_task_async

router = APIRouter()


# Pydantic models
class MemoryCreate(BaseModel):
    text: str = Field(..., description="Memory text content")
    type: str = Field(..., description="Type of memory")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    ttl_days: Optional[int] = Field(None, description="Time to live in days")


class MemoryUpdate(BaseModel):
    text: Optional[str] = Field(None, description="Memory text content")
    type: Optional[str] = Field(None, description="Type of memory")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    ttl_days: Optional[int] = Field(None, description="Time to live in days")


class MemoryResponse(BaseModel):
    id: uuid.UUID
    identity_id: uuid.UUID
    text: str
    type: str
    meta_data: Dict[str, Any]
    score: Optional[float]
    version: int
    ttl_days: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MemorySearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    type: Optional[str] = Field(None, description="Filter by memory type")
    limit: int = Field(default=10, description="Maximum number of results")
    similarity_threshold: float = Field(default=0.7, description="Minimum similarity score")


@router.post("/", response_model=MemoryResponse)
async def create_memory(
    memory_data: MemoryCreate,
    current_identity: Identity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db)
):
    """Create a new memory."""
    # Check permissions
    policy_engine = PolicyEngine(db)
    await policy_engine.check_memory_access(
        current_identity, 
        "write", 
        memory_type=memory_data.type,
        memory_metadata=memory_data.metadata
    )
    
    # Validate text length
    if len(memory_data.text) > 10000:  # 10KB limit
        raise ValidationError("Memory text too long (max 10KB)")
    
    # Create memory without vector initially
    memory = Memory(
        identity_id=current_identity.id,
        text=memory_data.text,
        type=memory_data.type,
        meta_data=memory_data.metadata,
        ttl_days=memory_data.ttl_days
    )
    
    db.add(memory)
    await db.commit()
    await db.refresh(memory)
    
    # Create audit log
    audit_log = AuditLog(
        event_type="memory.created",
        memory_id=memory.id,
        actor_id=current_identity.id,
        after_state={
            "text": memory.text,
            "type": memory.type,
            "metadata": memory.meta_data
        }
    )
    db.add(audit_log)
    await db.commit()
    
    # Trigger async embedding generation
    create_memory_embedding_task_async(str(memory.id))
    
    return MemoryResponse.from_orm(memory)


@router.get("/{memory_id}", response_model=MemoryResponse)
async def get_memory(
    memory_id: uuid.UUID,
    current_identity: Identity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db)
):
    """Get memory by ID."""
    stmt = select(Memory).where(
        and_(
            Memory.id == memory_id,
            Memory.is_deleted == False
        )
    )
    result = await db.execute(stmt)
    memory = result.scalar_one_or_none()
    
    if not memory:
        raise NotFoundError("Memory not found")
    
    # Check permissions
    policy_engine = PolicyEngine(db)
    await policy_engine.check_memory_access(
        current_identity, 
        "read", 
        memory_type=memory.type,
        memory_metadata=memory.meta_data
    )
    
    return MemoryResponse.from_orm(memory)


@router.get("/", response_model=List[MemoryResponse])
async def list_memories(
    skip: int = 0,
    limit: int = 100,
    type: Optional[str] = None,
    current_identity: Identity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db)
):
    """List memories for current identity."""
    stmt = select(Memory).where(
        and_(
            Memory.identity_id == current_identity.id,
            Memory.is_deleted == False
        )
    )
    
    if type:
        stmt = stmt.where(Memory.type == type)
    
    stmt = stmt.order_by(Memory.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    memories = result.scalars().all()
    
    return [MemoryResponse.from_orm(memory) for memory in memories]


@router.post("/search", response_model=List[MemoryResponse])
async def search_memories(
    search_request: MemorySearchRequest,
    current_identity: Identity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db)
):
    """Search memories using vector similarity."""
    # Check permissions
    policy_engine = PolicyEngine(db)
    await policy_engine.check_memory_access(
        current_identity, 
        "read", 
        memory_type=search_request.type
    )
    
    # Generate embedding for query
    try:
        query_embedding = await generate_embedding(search_request.query)
    except Exception as e:
        raise ValidationError(f"Failed to generate embedding: {str(e)}")
    
    # Build query
    stmt = select(Memory).where(
        and_(
            Memory.identity_id == current_identity.id,
            Memory.is_deleted == False
        )
    )
    
    if search_request.type:
        stmt = stmt.where(Memory.type == search_request.type)
    
    # Use text-based search since pgvector functions are not available
    stmt = stmt.where(Memory.text.ilike(f"%{search_request.query}%")).limit(search_request.limit)
    
    result = await db.execute(stmt)
    memories = result.scalars().all()
    
    # Use simple text-based scoring since vectors are not available
    filtered_memories = []
    for memory in memories:
        # Simple text similarity based on query presence
        query_lower = search_request.query.lower()
        text_lower = memory.text.lower()
        if query_lower in text_lower:
            memory.score = 0.8
        else:
            memory.score = 0.3
        filtered_memories.append(memory)
    
    return [MemoryResponse.from_orm(memory) for memory in filtered_memories]


@router.put("/{memory_id}", response_model=MemoryResponse)
async def update_memory(
    memory_id: uuid.UUID,
    memory_update: MemoryUpdate,
    current_identity: Identity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db)
):
    """Update memory."""
    stmt = select(Memory).where(
        and_(
            Memory.id == memory_id,
            Memory.identity_id == current_identity.id,
            Memory.is_deleted == False
        )
    )
    result = await db.execute(stmt)
    memory = result.scalar_one_or_none()
    
    if not memory:
        raise NotFoundError("Memory not found")
    
    # Check permissions
    policy_engine = PolicyEngine(db)
    await policy_engine.check_memory_access(
        current_identity, 
        "write", 
        memory_type=memory_update.type or memory.type,
        memory_metadata=memory_update.metadata or memory.metadata
    )
    
    # Store before state for audit
    before_state = {
        "text": memory.text,
        "type": memory.type,
        "metadata": memory.metadata,
        "version": memory.version
    }
    
    # Update memory
    update_data = memory_update.dict(exclude_unset=True)
    if update_data:
        for key, value in update_data.items():
            setattr(memory, key, value)
        
        memory.version += 1
        await db.commit()
        await db.refresh(memory)
        
        # Create audit log
        audit_log = AuditLog(
            event_type="memory.updated",
            memory_id=memory.id,
            actor_id=current_identity.id,
            before_state=before_state,
            after_state={
                "text": memory.text,
                "type": memory.type,
                "metadata": memory.metadata,
                "version": memory.version
            }
        )
        db.add(audit_log)
        await db.commit()
        
        # Regenerate embedding if text changed
        if "text" in update_data:
            create_memory_embedding_task_async(str(memory.id))
    
    return MemoryResponse.from_orm(memory)


@router.delete("/{memory_id}")
async def delete_memory(
    memory_id: uuid.UUID,
    hard_delete: bool = Query(False, description="Perform hard delete"),
    current_identity: Identity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db)
):
    """Delete memory (soft delete by default)."""
    stmt = select(Memory).where(
        and_(
            Memory.id == memory_id,
            Memory.identity_id == current_identity.id,
            Memory.is_deleted == False
        )
    )
    result = await db.execute(stmt)
    memory = result.scalar_one_or_none()
    
    if not memory:
        raise NotFoundError("Memory not found")
    
    # Check permissions
    policy_engine = PolicyEngine(db)
    await policy_engine.check_memory_access(
        current_identity, 
        "delete", 
        memory_type=memory.type,
        memory_metadata=memory.metadata
    )
    
    if hard_delete:
        # Hard delete
        await db.delete(memory)
        event_type = "memory.hard_deleted"
    else:
        # Soft delete
        memory.is_deleted = True
        memory.deleted_at = func.now()
        event_type = "memory.soft_deleted"
    
    # Create audit log
    audit_log = AuditLog(
        event_type=event_type,
        memory_id=memory.id,
        actor_id=current_identity.id,
        before_state={
            "text": memory.text,
            "type": memory.type,
            "metadata": memory.metadata
        }
    )
    db.add(audit_log)
    await db.commit()
    
    return {"message": "Memory deleted successfully"} 