"""
Webhook service for real-time notifications
"""

import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta
from typing import Any
from urllib.parse import urlparse

import httpx
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from manushya.db.models import Webhook, WebhookDelivery

logger = structlog.get_logger()


class WebhookService:
    """Service for managing webhook registrations and deliveries."""

    # Supported event types
    SUPPORTED_EVENTS = [
        "identity.created",
        "identity.updated",
        "identity.deleted",
        "memory.created",
        "memory.updated",
        "memory.deleted",
        "policy.created",
        "policy.updated",
        "policy.deleted",
        "api_key.created",
        "api_key.revoked",
        "invitation.sent",
        "invitation.accepted",
        "session.created",
        "session.revoked",
        "rate_limit.exceeded"
    ]

    # Retry configuration
    MAX_RETRY_ATTEMPTS = 5
    RETRY_DELAYS = [60, 300, 900, 3600, 7200]  # 1min, 5min, 15min, 1hr, 2hr

    @staticmethod
    def generate_secret() -> str:
        """Generate a secure webhook secret."""
        return secrets.token_urlsafe(32)

    @staticmethod
    def generate_signature(payload: str, secret: str) -> str:
        """Generate HMAC signature for webhook payload."""
        return hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

    @staticmethod
    async def create_webhook(
        db: AsyncSession,
        name: str,
        url: str,
        events: list[str],
        created_by: str | None = None,
        tenant_id: str | None = None
    ) -> Webhook:
        """Create a new webhook registration."""
        # Validate URL
        try:
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                raise ValueError("Invalid URL format")
        except Exception as e:
            raise ValueError(f"Invalid URL: {str(e)}") from e

        # Validate events
        invalid_events = [event for event in events if event not in WebhookService.SUPPORTED_EVENTS]
        if invalid_events:
            raise ValueError(f"Unsupported events: {invalid_events}")

        # Create webhook
        webhook = Webhook(
            name=name,
            url=url,
            events=events,
            secret=WebhookService.generate_secret(),
            created_by=created_by,
            tenant_id=tenant_id
        )

        db.add(webhook)
        await db.commit()
        await db.refresh(webhook)

        logger.info(
            "Webhook created",
            webhook_id=str(webhook.id),
            name=name,
            url=url,
            events=events
        )

        return webhook

    @staticmethod
    async def get_webhooks(
        db: AsyncSession,
        tenant_id: str | None = None,
        is_active: bool | None = None
    ) -> list[Webhook]:
        """Get webhooks with optional filtering."""
        stmt = select(Webhook)

        if tenant_id:
            stmt = stmt.where(Webhook.tenant_id == tenant_id)

        if is_active is not None:
            stmt = stmt.where(Webhook.is_active == is_active)

        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_webhook(db: AsyncSession, webhook_id: str) -> Webhook | None:
        """Get a specific webhook by ID."""
        stmt = select(Webhook).where(Webhook.id == webhook_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def update_webhook(
        db: AsyncSession,
        webhook_id: str,
        name: str | None = None,
        url: str | None = None,
        events: list[str] | None = None,
        is_active: bool | None = None
    ) -> Webhook | None:
        """Update a webhook."""
        webhook = await WebhookService.get_webhook(db, webhook_id)
        if not webhook:
            return None

        if name is not None:
            webhook.name = name
        if url is not None:
            # Validate URL
            try:
                parsed_url = urlparse(url)
                if not parsed_url.scheme or not parsed_url.netloc:
                    raise ValueError("Invalid URL format")
            except Exception as e:
                raise ValueError(f"Invalid URL: {str(e)}") from e
            webhook.url = url
        if events is not None:
            # Validate events
            invalid_events = [event for event in events if event not in WebhookService.SUPPORTED_EVENTS]
            if invalid_events:
                raise ValueError(f"Unsupported events: {invalid_events}")
            webhook.events = events
        if is_active is not None:
            webhook.is_active = is_active

        webhook.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(webhook)

        logger.info(
            "Webhook updated",
            webhook_id=str(webhook.id),
            name=webhook.name
        )

        return webhook

    @staticmethod
    async def delete_webhook(db: AsyncSession, webhook_id: str) -> bool:
        """Delete a webhook."""
        webhook = await WebhookService.get_webhook(db, webhook_id)
        if not webhook:
            return False

        await db.delete(webhook)
        await db.commit()

        logger.info(
            "Webhook deleted",
            webhook_id=str(webhook_id),
            name=webhook.name
        )

        return True

    @staticmethod
    async def trigger_webhook(
        db: AsyncSession,
        event_type: str,
        payload: dict[str, Any],
        tenant_id: str | None = None
    ) -> None:
        """Trigger webhooks for a specific event."""
        # Get active webhooks that subscribe to this event
        stmt = select(Webhook).where(
            Webhook.is_active,
            Webhook.events.contains([event_type])
        )

        if tenant_id:
            stmt = stmt.where(Webhook.tenant_id == tenant_id)

        result = await db.execute(stmt)
        webhooks = result.scalars().all()

        # Create delivery records for each webhook
        for webhook in webhooks:
            delivery = WebhookDelivery(
                webhook_id=webhook.id,
                event_type=event_type,
                payload=payload,
                tenant_id=tenant_id
            )
            db.add(delivery)

        await db.commit()

        # Trigger background tasks for delivery
        for webhook in webhooks:
            # Get the delivery record we just created
            stmt = select(WebhookDelivery).where(
                WebhookDelivery.webhook_id == webhook.id,
                WebhookDelivery.event_type == event_type
            ).order_by(WebhookDelivery.created_at.desc()).limit(1)

            result = await db.execute(stmt)
            delivery = result.scalar_one_or_none()

            if delivery:
                # Queue background task for delivery
                from manushya.tasks.webhook_tasks import deliver_webhook_task
                deliver_webhook_task.delay(str(delivery.id))

        logger.info(
            "Webhooks triggered",
            event_type=event_type,
            webhook_count=len(webhooks)
        )

    @staticmethod
    async def deliver_webhook(delivery_id: str, db: AsyncSession) -> bool:
        """Deliver a webhook (called by background task)."""
        # Get delivery record
        stmt = select(WebhookDelivery).where(WebhookDelivery.id == delivery_id)
        result = await db.execute(stmt)
        delivery = result.scalar_one_or_none()

        if not delivery:
            logger.error("Webhook delivery not found", delivery_id=delivery_id)
            return False

        # Get webhook
        webhook = await WebhookService.get_webhook(db, str(delivery.webhook_id))
        if not webhook or not webhook.is_active:
            delivery.status = "failed"
            delivery.response_body = "Webhook not found or inactive"
            await db.commit()
            return False

        # Prepare payload
        payload = {
            "event": delivery.event_type,
            "timestamp": delivery.created_at.isoformat(),
            "data": delivery.payload
        }

        payload_str = json.dumps(payload, sort_keys=True)
        signature = WebhookService.generate_signature(payload_str, webhook.secret)

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Manushya-Webhook/1.0",
            "X-Webhook-Signature": f"sha256={signature}",
            "X-Webhook-Event": delivery.event_type,
            "X-Webhook-Delivery": str(delivery.id)
        }

        # Attempt delivery
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    webhook.url,
                    content=payload_str,
                    headers=headers
                )

                delivery.response_code = response.status_code
                delivery.response_body = response.text[:1000]  # Limit response body
                delivery.delivery_attempts += 1

                if 200 <= response.status_code < 300:
                    delivery.status = "delivered"
                    delivery.delivered_at = datetime.utcnow()
                    logger.info(
                        "Webhook delivered successfully",
                        delivery_id=str(delivery.id),
                        webhook_id=str(webhook.id),
                        status_code=response.status_code
                    )
                else:
                    delivery.status = "failed"
                    logger.warning(
                        "Webhook delivery failed",
                        delivery_id=str(delivery.id),
                        webhook_id=str(webhook.id),
                        status_code=response.status_code,
                        response_text=response.text[:200]
                    )

        except Exception as e:
            delivery.status = "failed"
            delivery.response_body = str(e)[:1000]
            delivery.delivery_attempts += 1
            logger.error(
                "Webhook delivery error",
                delivery_id=str(delivery.id),
                webhook_id=str(webhook.id),
                error=str(e)
            )

        # Set up retry if needed
        if delivery.status == "failed" and delivery.delivery_attempts < WebhookService.MAX_RETRY_ATTEMPTS:
            delay = WebhookService.RETRY_DELAYS[min(delivery.delivery_attempts - 1, len(WebhookService.RETRY_DELAYS) - 1)]
            delivery.next_retry_at = datetime.utcnow() + timedelta(seconds=delay)
            delivery.status = "pending"

        await db.commit()
        return delivery.status == "delivered"

    @staticmethod
    async def retry_failed_deliveries(db: AsyncSession) -> int:
        """Retry failed webhook deliveries that are due for retry."""
        stmt = select(WebhookDelivery).where(
            WebhookDelivery.status == "pending",
            WebhookDelivery.next_retry_at <= datetime.utcnow(),
            WebhookDelivery.delivery_attempts < WebhookService.MAX_RETRY_ATTEMPTS
        )

        result = await db.execute(stmt)
        deliveries = result.scalars().all()

        retry_count = 0
        for delivery in deliveries:
            success = await WebhookService.deliver_webhook(str(delivery.id), db)
            if success:
                retry_count += 1

        logger.info(
            "Retried failed webhook deliveries",
            total=len(deliveries),
            successful=retry_count
        )

        return retry_count

    @staticmethod
    async def cleanup_old_deliveries(db: AsyncSession, days_old: int = 30) -> int:
        """Clean up old webhook delivery records."""
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)

        stmt = select(WebhookDelivery).where(
            WebhookDelivery.created_at < cutoff_date,
            WebhookDelivery.status.in_(["delivered", "failed"])
        )

        result = await db.execute(stmt)
        old_deliveries = result.scalars().all()

        cleaned_count = 0
        for delivery in old_deliveries:
            await db.delete(delivery)
            cleaned_count += 1

        await db.commit()

        logger.info(
            "Cleaned up old webhook deliveries",
            cleaned_count=cleaned_count,
            cutoff_date=cutoff_date.isoformat()
        )

        return cleaned_count

