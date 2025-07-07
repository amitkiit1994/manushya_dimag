"""
Identity events API endpoints for Manushya.ai
"""

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from manushya.core.auth import get_current_identity
from manushya.core.event_service import EventService
from manushya.core.exceptions import NotFoundError
from manushya.core.policy_engine import PolicyEngine
from manushya.db.database import get_db
from manushya.db.models import AuditLog, Identity, IdentityEvent

router = APIRouter()


# Pydantic models
class EventResponse(BaseModel):
    id: uuid.UUID
    event_type: str
    identity_id: uuid.UUID | None
    actor_id: uuid.UUID | None
    payload: dict[str, Any]
    metadata: dict[str, Any]
    is_delivered: bool
    delivery_attempts: int
    delivered_at: datetime | None
    created_at: datetime
    updated_at: datetime
    tenant_id: uuid.UUID | None = None

    class Config:
        from_attributes = True


class EventTypeInfo(BaseModel):
    event_type: str
    description: str


class EventStats(BaseModel):
    total_events: int
    delivered_events: int
    undelivered_events: int
    event_types: dict[str, int]


@router.get("/", response_model=list[EventResponse])
async def list_events(
    event_type: str | None = Query(None, description="Filter by event type"),
    identity_id: uuid.UUID | None = Query(None, description="Filter by identity ID"),
    is_delivered: bool | None = Query(None, description="Filter by delivery status"),
    limit: int = Query(100, description="Maximum number of events to return"),
    current_identity: Identity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
):
    """List identity events with optional filtering."""
    # Check permissions
    policy_engine = PolicyEngine(db)
    await policy_engine.check_identity_access(
        current_identity, "read", target_role="admin"
    )

    stmt = select(IdentityEvent)

    # Apply filters
    if event_type:
        stmt = stmt.where(IdentityEvent.event_type == event_type)

    if identity_id:
        stmt = stmt.where(IdentityEvent.identity_id == identity_id)

    if is_delivered is not None:
        stmt = stmt.where(IdentityEvent.is_delivered == is_delivered)

    # Tenant filtering
    if current_identity.tenant_id is not None:
        stmt = stmt.where(IdentityEvent.tenant_id == current_identity.tenant_id)
    # else: global/system-level identity can see all

    stmt = stmt.order_by(IdentityEvent.created_at.desc()).limit(limit)
    result = await db.execute(stmt)
    events = result.scalars().all()

    return [EventResponse.from_orm(event) for event in events]


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: uuid.UUID,
    current_identity: Identity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
):
    """Get specific event details."""
    # Check permissions
    policy_engine = PolicyEngine(db)
    await policy_engine.check_identity_access(
        current_identity, "read", target_role="admin"
    )

    stmt = select(IdentityEvent).where(IdentityEvent.id == event_id)
    # Tenant filtering
    if current_identity.tenant_id is not None:
        stmt = stmt.where(IdentityEvent.tenant_id == current_identity.tenant_id)
    # else: global/system-level identity can see all

    result = await db.execute(stmt)
    event = result.scalar_one_or_none()

    if not event:
        raise NotFoundError("Event not found")

    return EventResponse.from_orm(event)


@router.get("/identity/{identity_id}", response_model=list[EventResponse])
async def get_events_for_identity(
    identity_id: uuid.UUID,
    event_types: list[str] | None = Query(None, description="Filter by event types"),
    limit: int = Query(100, description="Maximum number of events to return"),
    current_identity: Identity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
):
    """Get events for a specific identity."""
    # Check permissions
    policy_engine = PolicyEngine(db)
    await policy_engine.check_identity_access(
        current_identity, "read", target_role="admin"
    )

    events = await EventService.get_events_for_identity(
        db=db,
        identity_id=str(identity_id),
        event_types=event_types,
        limit=limit
    )

    return [EventResponse.from_orm(event) for event in events]


@router.get("/types", response_model=list[EventTypeInfo])
async def get_event_types(
    current_identity: Identity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
):
    """Get list of available event types."""
    # Check permissions
    policy_engine = PolicyEngine(db)
    await policy_engine.check_identity_access(
        current_identity, "read", target_role="admin"
    )

    event_types = []
    for event_type, description in EventService.EVENT_TYPES.items():
        event_types.append(EventTypeInfo(
            event_type=event_type,
            description=description
        ))

    return event_types


@router.get("/stats", response_model=EventStats)
async def get_event_stats(
    current_identity: Identity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
):
    """Get event statistics."""
    # Check permissions
    policy_engine = PolicyEngine(db)
    await policy_engine.check_identity_access(
        current_identity, "read", target_role="admin"
    )

    # Build base query with tenant filtering
    base_stmt = select(IdentityEvent)
    if current_identity.tenant_id is not None:
        base_stmt = base_stmt.where(IdentityEvent.tenant_id == current_identity.tenant_id)

    # Total events
    result = await db.execute(base_stmt)
    total_events = len(result.scalars().all())

    # Delivered events
    delivered_stmt = base_stmt.where(IdentityEvent.is_delivered)
    result = await db.execute(delivered_stmt)
    delivered_events = len(result.scalars().all())

    # Undelivered events
    undelivered_stmt = base_stmt.where(~IdentityEvent.is_delivered)
    result = await db.execute(undelivered_stmt)
    undelivered_events = len(result.scalars().all())

    # Event types breakdown
    event_types_stmt = base_stmt
    result = await db.execute(event_types_stmt)
    all_events = result.scalars().all()

    event_types_count = {}
    for event in all_events:
        event_types_count[event.event_type] = event_types_count.get(event.event_type, 0) + 1

    return EventStats(
        total_events=total_events,
        delivered_events=delivered_events,
        undelivered_events=undelivered_events,
        event_types=event_types_count
    )


@router.post("/retry/{event_id}")
async def retry_event_delivery(
    event_id: uuid.UUID,
    current_identity: Identity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
):
    """Retry delivery of a failed event."""
    # Check permissions
    policy_engine = PolicyEngine(db)
    await policy_engine.check_identity_access(
        current_identity, "write", target_role="admin"
    )

    stmt = select(IdentityEvent).where(IdentityEvent.id == event_id)
    # Tenant filtering
    if current_identity.tenant_id is not None:
        stmt = stmt.where(IdentityEvent.tenant_id == current_identity.tenant_id)
    # else: global/system-level identity can see all

    result = await db.execute(stmt)
    event = result.scalar_one_or_none()

    if not event:
        raise NotFoundError("Event not found")

    if event.is_delivered:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Event is already delivered"
        )

    # Increment delivery attempts
    await EventService.increment_delivery_attempts(db, str(event_id))

    # Trigger retry delivery
    import asyncio
    asyncio.create_task(EventService._deliver_event(event))

    # Create audit log
    audit_log = AuditLog(
        event_type="event.retry_delivery",
        actor_id=current_identity.id,
        tenant_id=current_identity.tenant_id,
        meta_data={
            "event_id": str(event_id),
            "event_type": event.event_type,
            "delivery_attempts": event.delivery_attempts + 1,
        },
    )
    db.add(audit_log)
    await db.commit()

    return {"message": "Event delivery retry initiated"}


@router.post("/cleanup")
async def cleanup_old_events(
    days_old: int = Query(90, description="Remove events older than this many days"),
    current_identity: Identity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
):
    """Clean up old delivered events (admin only)."""
    # Check permissions
    policy_engine = PolicyEngine(db)
    await policy_engine.check_identity_access(
        current_identity, "delete", target_role="admin"
    )

    cleaned_count = await EventService.cleanup_old_events(db, days_old)

    # Create audit log
    audit_log = AuditLog(
        event_type="events.cleanup",
        actor_id=current_identity.id,
        tenant_id=current_identity.tenant_id,
        meta_data={
            "cleaned_count": cleaned_count,
            "days_old": days_old,
        },
    )
    db.add(audit_log)
    await db.commit()

    return {
        "message": f"Cleaned up {cleaned_count} old events",
        "cleaned_count": cleaned_count,
        "days_old": days_old
    }


@router.post("/test")
async def test_event_publishing(
    event_type: str = Query("test.event", description="Event type to test"),
    current_identity: Identity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
):
    """Test event publishing (admin only)."""
    # Check permissions
    policy_engine = PolicyEngine(db)
    await policy_engine.check_identity_access(
        current_identity, "write", target_role="admin"
    )

    # Publish test event
    event = await EventService.publish_event(
        db=db,
        event_type=event_type,
        identity_id=str(current_identity.id),
        actor_id=str(current_identity.id),
        payload={
            "test": True,
            "message": "This is a test event",
            "timestamp": datetime.utcnow().isoformat()
        },
        metadata={
            "source": "test_endpoint",
            "user_agent": "test"
        },
        tenant_id=str(current_identity.tenant_id) if current_identity.tenant_id else None
    )

    return {
        "message": "Test event published successfully",
        "event_id": str(event.id),
        "event_type": event.event_type,
        "payload": EventService.format_event_payload(event)
    }
