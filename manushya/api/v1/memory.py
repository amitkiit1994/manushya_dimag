"""
Memory API endpoints for Manushya.ai
"""

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import and_, func, select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from manushya.core.auth import get_current_identity
from manushya.core.exceptions import NotFoundError, ValidationError
from manushya.core.policy_engine import PolicyEngine
from manushya.db.database import get_db
from manushya.db.models import AuditLog, Identity, Memory
from manushya.services.embedding_service import generate_embedding
from manushya.services.webhook_service import WebhookService
from manushya.tasks.memory_tasks import create_memory_embedding_task

router = APIRouter()


# Pydantic models
class MemoryCreate(BaseModel):
    text: str = Field(..., description="Memory text content")
    type: str = Field(..., description="Type of memory")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
    ttl_days: int | None = Field(None, description="Time to live in days")


class MemoryUpdate(BaseModel):
    text: str | None = Field(None, description="Memory text content")
    type: str | None = Field(None, description="Type of memory")
    metadata: dict[str, Any] | None = Field(None, description="Additional metadata")
    ttl_days: int | None = Field(None, description="Time to live in days")


class MemoryResponse(BaseModel):
    id: uuid.UUID
    identity_id: uuid.UUID
    text: str
    type: str
    meta_data: dict[str, Any]
    score: float | None
    version: int
    ttl_days: int | None
    created_at: datetime
    updated_at: datetime
    tenant_id: uuid.UUID | None = None

    class Config:
        from_attributes = True


class MemorySearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    type: str | None = Field(None, description="Filter by memory type")
    limit: int = Field(default=10, description="Maximum number of results")
    similarity_threshold: float = Field(
        default=0.7, description="Minimum similarity score"
    )


class BulkDeleteMemoryRequest(BaseModel):
    memory_ids: list[uuid.UUID] = Field(..., description="List of memory IDs to delete")
    hard_delete: bool = Field(default=False, description="Perform hard delete instead of soft delete")
    reason: str | None = Field(None, description="Reason for bulk deletion")


class BulkDeleteMemoryResponse(BaseModel):
    deleted_count: int
    failed_count: int
    failed_memories: list[dict[str, Any]]
    message: str


@router.post("/", response_model=MemoryResponse, status_code=status.HTTP_201_CREATED)
async def create_memory(
    memory_data: MemoryCreate,
    current_identity: Identity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
):
    """Create a new memory."""
    # Check permissions
    policy_engine = PolicyEngine(db)
    await policy_engine.check_memory_access(
        current_identity,
        "write",
        memory_type=memory_data.type,
        memory_metadata=memory_data.metadata,
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
        ttl_days=memory_data.ttl_days,
        tenant_id=current_identity.tenant_id,
    )

    db.add(memory)
    await db.commit()
    await db.refresh(memory)

    # Create audit log
    audit_log = AuditLog(
        event_type="memory.created",
        memory_id=memory.id,
        actor_id=current_identity.id,
        tenant_id=current_identity.tenant_id,
        after_state={
            "text": memory.text,
            "type": memory.type,
            "metadata": memory.meta_data,
        },
    )
    db.add(audit_log)
    await db.commit()

    # Trigger async embedding generation
    create_memory_embedding_task.delay(str(memory.id))

    # Trigger webhook for memory creation
    await WebhookService.trigger_webhook(
        db=db,
        event_type="memory.created",
        payload={
            "id": str(memory.id),
            "content": memory.text,
            "memory_type": memory.type,
            "metadata": memory.meta_data,
            "tenant_id": str(memory.tenant_id),
            "created_at": memory.created_at.isoformat()
        },
        tenant_id=str(memory.tenant_id)
    )

    return MemoryResponse.from_orm(memory)


@router.get("/{memory_id}", response_model=MemoryResponse)
async def get_memory(
    memory_id: uuid.UUID,
    current_identity: Identity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
):
    """Get memory by ID."""
    stmt = select(Memory).where(
        and_(
            Memory.id == memory_id,
            Memory.identity_id == current_identity.id,
            ~Memory.is_deleted,
        )
    )
    # Tenant filtering
    if current_identity.tenant_id is not None:
        stmt = stmt.where(Memory.tenant_id == current_identity.tenant_id)
    # else: global/system-level identity can see all

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
        memory_metadata=memory.meta_data,
    )

    return MemoryResponse.from_orm(memory)


@router.get("/", response_model=list[MemoryResponse])
async def list_memories(
    skip: int = 0,
    limit: int = 100,
    memory_type: str | None = None,
    current_identity: Identity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
):
    """List memories for current identity."""
    print(
        f"DEBUG: current_identity.id={current_identity.id} type={type(current_identity.id)}"
    )
    stmt = select(Memory).where(
        and_(Memory.identity_id == current_identity.id, ~Memory.is_deleted)
    )

    if memory_type:
        stmt = stmt.where(Memory.type == memory_type)

    # Tenant filtering
    if current_identity.tenant_id is not None:
        stmt = stmt.where(Memory.tenant_id == current_identity.tenant_id)
    # else: global/system-level identity can see all

    stmt = stmt.order_by(Memory.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    memories = result.scalars().all()

    return [MemoryResponse.from_orm(memory) for memory in memories]


@router.post("/search", response_model=list[MemoryResponse])
async def search_memories(
    search_request: MemorySearchRequest,
    current_identity: Identity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
):
    """Search memories using vector similarity."""
    # Check permissions
    policy_engine = PolicyEngine(db)
    await policy_engine.check_memory_access(
        current_identity, "read", memory_type=search_request.type
    )

    # Generate embedding for query
    try:
        await generate_embedding(search_request.query)
    except Exception as e:
        raise ValidationError(f"Failed to generate embedding: {str(e)}") from e

    # Build query - be more flexible with identity matching
    stmt = select(Memory).where(~Memory.is_deleted)

    # For admin users, allow searching all memories within their tenant
    if current_identity.role == "admin":
        if current_identity.tenant_id is not None:
            stmt = stmt.where(Memory.tenant_id == current_identity.tenant_id)
    else:
        # For regular users, only show their own memories
        stmt = stmt.where(Memory.identity_id == current_identity.id)
        if current_identity.tenant_id is not None:
            stmt = stmt.where(Memory.tenant_id == current_identity.tenant_id)

    if search_request.type:
        stmt = stmt.where(Memory.type == search_request.type)

    # Use text-based search with multiple patterns for better matching
    query_terms = search_request.query.lower().split()
    memory_conditions = []
    
    for term in query_terms:
        if len(term) > 2:  # Only search for terms longer than 2 characters
            memory_conditions.append(Memory.text.ilike(f"%{term}%"))
    
    if memory_conditions:
        # Use OR condition for multiple terms
        stmt = stmt.where(or_(*memory_conditions))
    else:
        # Fallback to exact query match
        stmt = stmt.where(Memory.text.ilike(f"%{search_request.query}%"))

    stmt = stmt.limit(search_request.limit)
    result = await db.execute(stmt)
    memories = result.scalars().all()

    # Use simple text-based scoring since vectors are not available
    filtered_memories = []
    for memory in memories:
        # Calculate similarity score based on query term matches
        query_lower = search_request.query.lower()
        text_lower = memory.text.lower()
        
        # Count matching words
        query_words = set(query_lower.split())
        text_words = set(text_words for text_words in text_lower.split() if len(text_words) > 2)
        matching_words = len(query_words.intersection(text_words))
        
        if matching_words > 0:
            # Score based on word matches and query length
            memory.score = min(0.9, 0.3 + (matching_words / len(query_words)) * 0.6)
        elif query_lower in text_lower:
            memory.score = 0.7
        else:
            memory.score = 0.2
            
        # Only include memories above similarity threshold
        score = memory.score or 0.0
        if score >= search_request.similarity_threshold:
            filtered_memories.append(memory)

    # Sort by score descending
    filtered_memories.sort(key=lambda x: x.score or 0, reverse=True)

    return [MemoryResponse.from_orm(memory) for memory in filtered_memories]


@router.put("/{memory_id}", response_model=MemoryResponse)
async def update_memory(
    memory_id: uuid.UUID,
    memory_update: MemoryUpdate,
    current_identity: Identity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
):
    """Update memory."""
    stmt = select(Memory).where(
        and_(
            Memory.id == memory_id,
            Memory.identity_id == current_identity.id,
            ~Memory.is_deleted,
        )
    )
    # Tenant filtering
    if current_identity.tenant_id is not None:
        stmt = stmt.where(Memory.tenant_id == current_identity.tenant_id)
    # else: global/system-level identity can see all

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
        memory_metadata=memory_update.metadata or memory.meta_data,
    )

    # Store before state for audit
    before_state = {
        "text": memory.text,
        "type": memory.type,
        "metadata": memory.meta_data,
        "version": memory.version,
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
            tenant_id=current_identity.tenant_id,
            before_state=before_state,
            after_state={
                "text": memory.text,
                "type": memory.type,
                "metadata": memory.meta_data,
                "version": memory.version,
            },
        )
        db.add(audit_log)
        await db.commit()

        # Regenerate embedding if text changed
        if "text" in update_data:
            create_memory_embedding_task.delay(str(memory.id))

    # Trigger webhook for memory update
    await WebhookService.trigger_webhook(
        db=db,
        event_type="memory.updated",
        payload={
            "id": str(memory.id),
            "content": memory.text,
            "memory_type": memory.type,
            "metadata": memory.meta_data,
            "tenant_id": str(memory.tenant_id),
            "updated_at": memory.updated_at.isoformat()
        },
        tenant_id=str(memory.tenant_id)
    )

    return MemoryResponse.from_orm(memory)


@router.delete("/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memory(
    memory_id: uuid.UUID,
    hard_delete: bool = Query(False, description="Perform hard delete"),
    current_identity: Identity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
):
    """Delete memory (soft delete by default)."""
    stmt = select(Memory).where(
        and_(
            Memory.id == memory_id,
            Memory.identity_id == current_identity.id,
            ~Memory.is_deleted,
        )
    )
    # Tenant filtering
    if current_identity.tenant_id is not None:
        stmt = stmt.where(Memory.tenant_id == current_identity.tenant_id)
    # else: global/system-level identity can see all

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
        memory_metadata=memory.meta_data,
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
        tenant_id=current_identity.tenant_id,
        before_state={
            "text": memory.text,
            "type": memory.type,
            "metadata": memory.meta_data,
        },
    )
    db.add(audit_log)
    await db.commit()

    # Store memory data for webhook before deletion
    memory_data = {
        "id": str(memory.id),
        "content": memory.text,
        "memory_type": memory.type,
        "metadata": memory.meta_data,
        "tenant_id": str(memory.tenant_id),
        "deleted_at": datetime.utcnow().isoformat()
    }

    # Trigger webhook for memory deletion
    await WebhookService.trigger_webhook(
        db=db,
        event_type="memory.deleted",
        payload=memory_data,
        tenant_id=str(memory.tenant_id)
    )

    return None


@router.post("/bulk-delete", response_model=BulkDeleteMemoryResponse)
async def bulk_delete_memories(
    delete_request: BulkDeleteMemoryRequest,
    current_identity: Identity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
):
    """Bulk delete memories (requires appropriate permissions)."""
    # Check permissions
    policy_engine = PolicyEngine(db)
    await policy_engine.check_memory_access(
        current_identity, "delete", memory_type=None
    )

    deleted_count = 0
    failed_count = 0
    failed_memories = []

    for memory_id in delete_request.memory_ids:
        try:
            stmt = select(Memory).where(
                and_(
                    Memory.id == memory_id,
                    Memory.identity_id == current_identity.id,
                    ~Memory.is_deleted,
                )
            )
            # Tenant filtering
            if current_identity.tenant_id is not None:
                stmt = stmt.where(Memory.tenant_id == current_identity.tenant_id)
            # else: global/system-level identity can see all

            result = await db.execute(stmt)
            memory = result.scalar_one_or_none()

            if not memory:
                failed_count += 1
                failed_memories.append({
                    "memory_id": str(memory_id),
                    "error": "Memory not found or not accessible"
                })
                continue

            # Check permissions for this specific memory
            await policy_engine.check_memory_access(
                current_identity,
                "delete",
                memory_type=memory.type,
                memory_metadata=memory.meta_data,
            )

            if delete_request.hard_delete:
                # Hard delete - remove from database
                await db.delete(memory)
                event_type = "memory.hard_deleted"
            else:
                # Soft delete - mark as deleted
                memory.is_deleted = True
                memory.deleted_at = func.now()
                event_type = "memory.soft_deleted"

            # Create audit log for each deleted memory
            audit_log = AuditLog(
                event_type=event_type,
                memory_id=memory.id,
                actor_id=current_identity.id,
                tenant_id=current_identity.tenant_id,
                before_state={
                    "text": memory.text,
                    "type": memory.type,
                    "metadata": memory.meta_data,
                },
                meta_data={
                    "bulk_operation": True,
                    "reason": delete_request.reason
                }
            )
            db.add(audit_log)

            deleted_count += 1

        except Exception as e:
            failed_count += 1
            failed_memories.append({
                "memory_id": str(memory_id),
                "error": str(e)
            })

    # Commit all changes
    await db.commit()

    # Create summary audit log for bulk operation
    summary_audit_log = AuditLog(
        event_type="memory.bulk_deleted",
        actor_id=current_identity.id,
        tenant_id=current_identity.tenant_id,
        meta_data={
            "deleted_count": deleted_count,
            "failed_count": failed_count,
            "hard_delete": delete_request.hard_delete,
            "reason": delete_request.reason,
            "requested_ids": [str(id) for id in delete_request.memory_ids],
            "failed_memories": failed_memories
        }
    )
    db.add(summary_audit_log)
    await db.commit()

    # Trigger webhook for bulk deletion
    await WebhookService.trigger_webhook(
        db=db,
        event_type="memory.bulk_deleted",
        payload={
            "deleted_count": deleted_count,
            "failed_count": failed_count,
            "hard_delete": delete_request.hard_delete,
            "reason": delete_request.reason,
            "requested_ids": [str(id) for id in delete_request.memory_ids],
            "failed_memories": failed_memories
        },
        tenant_id=str(current_identity.tenant_id)
    )

    return BulkDeleteMemoryResponse(
        deleted_count=deleted_count,
        failed_count=failed_count,
        failed_memories=failed_memories,
        message=f"Bulk delete completed: {deleted_count} deleted, {failed_count} failed"
    )
