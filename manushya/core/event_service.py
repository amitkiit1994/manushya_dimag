"""
Identity event service for Manushya.ai
"""

import asyncio
from datetime import datetime
from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from manushya.db.models import IdentityEvent

logger = structlog.get_logger()


class EventService:
    """Service for managing identity lifecycle events."""

    # Standard event types
    EVENT_TYPES = {
        # Identity lifecycle events
        "identity.created": "Identity was created",
        "identity.updated": "Identity was updated",
        "identity.deleted": "Identity was deleted",
        "identity.activated": "Identity was activated",
        "identity.deactivated": "Identity was deactivated",

        # Session events
        "session.created": "New session created",
        "session.revoked": "Session was revoked",
        "session.expired": "Session expired",

        # API Key events
        "api_key.created": "API key was created",
        "api_key.revoked": "API key was revoked",
        "api_key.expired": "API key expired",

        # Invitation events
        "invitation.created": "Invitation was created",
        "invitation.accepted": "Invitation was accepted",
        "invitation.expired": "Invitation expired",
        "invitation.revoked": "Invitation was revoked",

        # Policy events
        "policy.created": "Policy was created",
        "policy.updated": "Policy was updated",
        "policy.deleted": "Policy was deleted",

        # Memory events
        "memory.created": "Memory was created",
        "memory.updated": "Memory was updated",
        "memory.deleted": "Memory was deleted",
    }

    @staticmethod
    async def publish_event(
        db: AsyncSession,
        event_type: str,
        identity_id: str | None = None,
        actor_id: str | None = None,
        payload: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        tenant_id: str | None = None
    ) -> IdentityEvent:
        """Publish an identity event."""
        if event_type not in EventService.EVENT_TYPES:
            logger.warning(f"Unknown event type: {event_type}")

        # Create event
        event = IdentityEvent(
            event_type=event_type,
            identity_id=identity_id,
            actor_id=actor_id,
            payload=payload or {},
            metadata=metadata or {},
            tenant_id=tenant_id,
        )

        db.add(event)
        await db.commit()
        await db.refresh(event)

        logger.info(
            "Identity event published",
            event_id=str(event.id),
            event_type=event_type,
            identity_id=identity_id,
            actor_id=actor_id,
            tenant_id=tenant_id
        )

        # Trigger async delivery
        asyncio.create_task(EventService._deliver_event(event))

        return event

    @staticmethod
    async def _deliver_event(event: IdentityEvent) -> None:
        """Deliver event to webhooks and external systems."""
        try:
            # In production, this would:
            # 1. Send to webhook endpoints
            # 2. Send to message queues (Redis, RabbitMQ, etc.)
            # 3. Send to event streaming platforms (Kafka, etc.)
            # 4. Update real-time dashboards

            logger.info(
                "Event delivery started",
                event_id=str(event.id),
                event_type=event.event_type
            )

            # Simulate delivery delay
            await asyncio.sleep(0.1)

            # Mark as delivered
            # Note: In a real implementation, this would be done in a separate task
            # that handles the actual delivery and updates the database
            logger.info(
                "Event delivered successfully",
                event_id=str(event.id),
                event_type=event.event_type
            )

        except Exception as e:
            logger.error(
                "Event delivery failed",
                event_id=str(event.id),
                event_type=event.event_type,
                error=str(e)
            )

    @staticmethod
    async def get_events_for_identity(
        db: AsyncSession,
        identity_id: str,
        event_types: list[str] | None = None,
        limit: int = 100
    ) -> list[IdentityEvent]:
        """Get events for a specific identity."""
        stmt = select(IdentityEvent).where(IdentityEvent.identity_id == identity_id)

        if event_types:
            stmt = stmt.where(IdentityEvent.event_type.in_(event_types))

        stmt = stmt.order_by(IdentityEvent.created_at.desc()).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_events_by_type(
        db: AsyncSession,
        event_type: str,
        tenant_id: str | None = None,
        limit: int = 100
    ) -> list[IdentityEvent]:
        """Get events by type, optionally filtered by tenant."""
        stmt = select(IdentityEvent).where(IdentityEvent.event_type == event_type)

        if tenant_id:
            stmt = stmt.where(IdentityEvent.tenant_id == tenant_id)

        stmt = stmt.order_by(IdentityEvent.created_at.desc()).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_undelivered_events(
        db: AsyncSession,
        limit: int = 100
    ) -> list[IdentityEvent]:
        """Get undelivered events for retry."""
        stmt = select(IdentityEvent).where(
            ~IdentityEvent.is_delivered,
            IdentityEvent.delivery_attempts < 3  # Max 3 attempts
        ).order_by(IdentityEvent.created_at.asc()).limit(limit)

        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def mark_event_delivered(
        db: AsyncSession,
        event_id: str
    ) -> bool:
        """Mark an event as delivered."""
        stmt = select(IdentityEvent).where(IdentityEvent.id == event_id)
        result = await db.execute(stmt)
        event = result.scalar_one_or_none()

        if not event:
            return False

        event.is_delivered = True
        event.delivered_at = datetime.utcnow()
        await db.commit()

        return True

    @staticmethod
    async def increment_delivery_attempts(
        db: AsyncSession,
        event_id: str
    ) -> bool:
        """Increment delivery attempts for an event."""
        stmt = select(IdentityEvent).where(IdentityEvent.id == event_id)
        result = await db.execute(stmt)
        event = result.scalar_one_or_none()

        if not event:
            return False

        event.delivery_attempts += 1
        await db.commit()

        return True

    @staticmethod
    def format_event_payload(event: IdentityEvent) -> dict[str, Any]:
        """Format event for webhook delivery."""
        return {
            "id": str(event.id),
            "event_type": event.event_type,
            "identity_id": str(event.identity_id) if event.identity_id else None,
            "actor_id": str(event.actor_id) if event.actor_id else None,
            "payload": event.payload,
            "metadata": event.metadata,
            "tenant_id": str(event.tenant_id) if event.tenant_id else None,
            "created_at": event.created_at.isoformat(),
            "timestamp": event.created_at.timestamp(),
        }

    @staticmethod
    async def cleanup_old_events(
        db: AsyncSession,
        days_old: int = 90
    ) -> int:
        """Clean up old events (admin only)."""
        from datetime import timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=days_old)

        stmt = select(IdentityEvent).where(
            IdentityEvent.created_at < cutoff_date,
            IdentityEvent.is_delivered
        )

        result = await db.execute(stmt)
        old_events = result.scalars().all()

        cleaned_count = 0
        for event in old_events:
            await db.delete(event)
            cleaned_count += 1

        await db.commit()

        logger.info(
            "Cleaned up old events",
            cleaned_count=cleaned_count,
            cutoff_date=cutoff_date.isoformat()
        )

        return cleaned_count
