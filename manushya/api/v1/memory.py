"""
Memory API endpoints for Manushya.ai
"""

import logging
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from manushya.core.auth import get_current_identity
from manushya.core.exceptions import NotFoundError, ValidationError
from manushya.core.policy_engine import PolicyEngine
from manushya.db.database import get_db
from manushya.db.models import AuditLog, Identity, Memory
from manushya.services.embedding import EmbeddingService
from manushya.services.embedding_service import generate_embedding
from manushya.services.usage_service import UsageService
from manushya.services.webhook_service import WebhookService
from manushya.tasks.memory_tasks import create_memory_embedding_task

logger = logging.getLogger(__name__)
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
    hard_delete: bool = Field(
        default=False, description="Perform hard delete instead of soft delete"
    )
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
    from manushya.core.exceptions import AccessDeniedError
    try:
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
        # Generate embedding synchronously for immediate search capability
        embedding = None
        try:
            embedding = await generate_embedding(memory_data.text)
            # Convert to list for storage
            embedding_list = list(embedding) if embedding else None
        except Exception as e:
            logger.warning(f"Failed to generate embedding for memory: {e}")
            embedding_list = None
        # Create memory with embedding
        memory = Memory(
            identity_id=current_identity.id,
            text=memory_data.text,
            type=memory_data.type,
            meta_data=memory_data.metadata,
            ttl_days=memory_data.ttl_days,
            tenant_id=current_identity.tenant_id,
            vector=embedding_list,
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
        # Track usage for memory creation
        if current_identity.tenant_id:
            usage_service = UsageService(db)
            await usage_service.track_event(
                tenant_id=current_identity.tenant_id,
                event="memory.write",
                units=1,
                identity_id=current_identity.id,
                metadata={
                    "memory_id": str(memory.id),
                    "memory_type": memory.type,
                    "text_length": len(memory.text),
                    "embedding_generated": embedding is not None,
                },
            )
        # Trigger webhook for memory creation
        await WebhookService.trigger_webhook(
            db=db,
            event_type="memory.created",
            payload={
                "id": str(memory.id),
                "content": memory.text,
                "memory_type": memory.type,
                "metadata": memory.meta_data,
                "embedding_generated": embedding is not None,
                "tenant_id": str(memory.tenant_id),
                "created_at": memory.created_at.isoformat(),
            },
            tenant_id=str(memory.tenant_id),
        )
        logger.info(f"Created memory {memory.id} with embedding: {embedding is not None}")
        return MemoryResponse.from_orm(memory)
    except AccessDeniedError as ade:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail=str(ade))
    except Exception as e:
        logger.error(f"Unexpected error in create_memory: {e}")
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail="Internal server error")


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
    """Search memories using vector similarity and text matching."""
    # Check permissions
    policy_engine = PolicyEngine(db)
    await policy_engine.check_memory_access(
        current_identity, "read", memory_type=search_request.type
    )
    # Generate embedding for query
    try:
        query_embedding = await generate_embedding(search_request.query)
    except Exception as e:
        logger.warning(
            f"Failed to generate embedding: {e}, falling back to text search"
        )
        query_embedding = None
    # Build query with flexible identity matching
    stmt = select(Memory).where(~Memory.is_deleted)
    # For admin users, allow access to all memories within tenant
    if current_identity.role == "admin":
        stmt = stmt.where(Memory.tenant_id == current_identity.tenant_id)
    else:
        # For non-admin users, only show their own memories
        stmt = stmt.where(Memory.identity_id == current_identity.id)
    # Add type filter if specified
    if search_request.type:
        stmt = stmt.where(Memory.type == search_request.type)
    # Add text search if no embedding available
    if query_embedding is None:
        # Use word-based search instead of simple substring
        search_terms = search_request.query.lower().split()
        conditions = []
        for term in search_terms:
            if len(term) > 2:  # Only search for terms longer than 2 chars
                conditions.append(Memory.text.ilike(f"%{term}%"))
        if conditions:
            stmt = stmt.where(or_(*conditions))
    # Execute query
    result = await db.execute(stmt)
    memories = result.scalars().all()
    # Calculate similarity scores if embedding is available
    if query_embedding and memories:
        for memory in memories:
            if memory.vector:
                try:
                    # Use vector directly
                    memory_embedding = memory.vector
                    # Calculate cosine similarity
                    embedding_service = EmbeddingService()
                    similarity = embedding_service.calculate_similarity(query_embedding, memory_embedding)
                    memory.score = similarity
                except Exception as e:
                    logger.warning(
                        f"Failed to calculate similarity for memory {memory.id}: {e}"
                    )
                    memory.score = 0.0
            else:
                memory.score = 0.0
    # Sort by similarity score (descending) if available, otherwise by creation date
    if query_embedding:
        memories = sorted(memories, key=lambda m: m.score or 0.0, reverse=True)
    else:
        memories = sorted(memories, key=lambda m: m.created_at, reverse=True)
    # Apply similarity threshold and limit
    filtered_memories = []
    for memory in memories:
        score = memory.score or 0.0
        if score >= search_request.similarity_threshold:
            filtered_memories.append(memory)
        elif memory.score is None:
            # Include memories without scores if they match the query
            filtered_memories.append(memory)
    # Apply limit
    filtered_memories = filtered_memories[: search_request.limit]
    # Track usage for memory search
    if current_identity.tenant_id:
        usage_service = UsageService(db)
        await usage_service.track_event(
            tenant_id=current_identity.tenant_id,
            event="memory.search",
            units=1,
            identity_id=current_identity.id,
            metadata={
                "query": search_request.query,
                "memory_type": search_request.type,
                "limit": search_request.limit,
                "similarity_threshold": search_request.similarity_threshold,
                "results_count": len(filtered_memories),
                "total_memories": len(memories),
                "embedding_used": query_embedding is not None,
            },
        )
    logger.info(
        f"Memory search completed: {len(filtered_memories)} results from {len(memories)} total memories"
    )
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
            "updated_at": memory.updated_at.isoformat(),
        },
        tenant_id=str(memory.tenant_id),
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
        "deleted_at": datetime.utcnow().isoformat(),
    }
    # Trigger webhook for memory deletion
    await WebhookService.trigger_webhook(
        db=db,
        event_type="memory.deleted",
        payload=memory_data,
        tenant_id=str(memory.tenant_id),
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
                failed_memories.append(
                    {
                        "memory_id": str(memory_id),
                        "error": "Memory not found or not accessible",
                    }
                )
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
                meta_data={"bulk_operation": True, "reason": delete_request.reason},
            )
            db.add(audit_log)
            deleted_count += 1
        except Exception as e:
            failed_count += 1
            failed_memories.append(
                {
                    "memory_id": str(memory_id),
                    "error": str(e),
                }
            )
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
            "failed_memories": failed_memories,
        },
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
            "failed_memories": failed_memories,
        },
        tenant_id=str(current_identity.tenant_id),
    )
    return BulkDeleteMemoryResponse(
        deleted_count=deleted_count,
        failed_count=failed_count,
        failed_memories=failed_memories,
        message=(
            f"Bulk delete completed: {deleted_count} deleted, {failed_count} failed"
        ),
    )
