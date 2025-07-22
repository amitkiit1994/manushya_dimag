"""
Production-grade webhook service with retry logic and delivery tracking
"""

import asyncio
import hashlib
import hmac
import logging
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import urlparse

import httpx
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from manushya.db.models import Webhook, WebhookDelivery
# Removed circular import - will use celery_app directly if needed

logger = logging.getLogger(__name__)
# Webhook delivery configurations
WEBHOOK_CONFIG = {
    "max_retries": 5,
    "initial_delay": 1.0,  # seconds
    "max_delay": 300.0,  # 5 minutes
    "backoff_factor": 2.0,
    "timeout": 30.0,  # seconds
    "batch_size": 100,
    "max_concurrent": 10,
}


class WebhookService:
    """Production-grade webhook service with retry logic and delivery tracking."""

    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def generate_secret() -> str:
        """Generate a secure webhook secret."""
        return secrets.token_urlsafe(32)

    @staticmethod
    def generate_signature(payload: str, secret: str) -> str:
        """Generate HMAC signature for webhook payload."""
        return hmac.new(
            secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256
        ).hexdigest()

    @staticmethod
    async def create_webhook(
        db: AsyncSession,
        name: str,
        url: str,
        events: list[str],
        created_by: str | None = None,
        tenant_id: str | None = None,
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
        invalid_events = [
            event for event in events if event not in WebhookService.SUPPORTED_EVENTS
        ]
        if invalid_events:
            raise ValueError(f"Unsupported events: {invalid_events}")
        # Create webhook
        webhook = Webhook(
            name=name,
            url=url,
            events=events,
            secret=WebhookService.generate_secret(),
            created_by=created_by,
            tenant_id=tenant_id,
        )
        db.add(webhook)
        await db.commit()
        await db.refresh(webhook)
        logger.info(
            "Webhook created",
            webhook_id=str(webhook.id),
            name=name,
            url=url,
            events=events,
        )
        return webhook

    @staticmethod
    async def get_webhooks(
        db: AsyncSession, tenant_id: str | None = None, is_active: bool | None = None
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
        is_active: bool | None = None,
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
            invalid_events = [
                event
                for event in events
                if event not in WebhookService.SUPPORTED_EVENTS
            ]
            if invalid_events:
                raise ValueError(f"Unsupported events: {invalid_events}")
            webhook.events = events
        if is_active is not None:
            webhook.is_active = is_active
        webhook.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(webhook)
        logger.info("Webhook updated", webhook_id=str(webhook.id), name=webhook.name)
        return webhook

    @staticmethod
    async def delete_webhook(db: AsyncSession, webhook_id: str) -> bool:
        """Delete a webhook."""
        webhook = await WebhookService.get_webhook(db, webhook_id)
        if not webhook:
            return False
        await db.delete(webhook)
        await db.commit()
        logger.info("Webhook deleted", webhook_id=str(webhook_id), name=webhook.name)
        return True

    @staticmethod
    async def trigger_webhook(
        db: AsyncSession,
        event_type: str,
        payload: dict[str, Any],
        tenant_id: str,
        webhook_id: str | None = None,
    ) -> None:
        """
        Trigger webhooks for an event with async processing.
        Args:
            db: Database session
            event_type: Type of event (e.g., "identity.created")
            payload: Event payload
            tenant_id: Tenant ID for filtering webhooks
            webhook_id: Specific webhook ID to trigger (optional)
        """
        try:
            # Get webhooks for this event type and tenant
            webhooks = await WebhookService._get_webhooks_for_event(
                db, event_type, tenant_id, webhook_id
            )
            if not webhooks:
                logger.debug(
                    f"No webhooks found for event {event_type} in tenant {tenant_id}"
                )
                return
            # Create delivery records and queue tasks
            for webhook in webhooks:
                delivery = await WebhookService._create_delivery_record(
                    db, webhook, event_type, payload
                )
                # Queue async delivery task
                try:
                    # Import here to avoid circular import
                    from manushya.tasks.webhook_tasks import deliver_webhook_task
                    deliver_webhook_task.delay(str(delivery.id))
                    logger.info(
                        f"Queued webhook delivery {delivery.id} for {webhook.url}"
                    )
                except Exception as e:
                    logger.error(f"Failed to queue webhook delivery: {e}")
                    # Mark delivery as failed
                    delivery.status = "failed"
                    delivery.error_message = f"Failed to queue: {str(e)}"
                    await db.commit()
        except Exception as e:
            logger.error(f"Failed to trigger webhooks for event {event_type}: {e}")

    @staticmethod
    async def _get_webhooks_for_event(
        db: AsyncSession,
        event_type: str,
        tenant_id: str,
        webhook_id: str | None = None,
    ) -> list[Webhook]:
        """Get active webhooks for an event type."""
        stmt = select(Webhook).where(
            and_(
                Webhook.is_active,
                Webhook.tenant_id == tenant_id,
                Webhook.events.contains([event_type]),
            )
        )
        if webhook_id:
            stmt = stmt.where(Webhook.id == webhook_id)
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def _create_delivery_record(
        db: AsyncSession, webhook: Webhook, event_type: str, payload: dict[str, Any]
    ) -> WebhookDelivery:
        """Create a webhook delivery record."""
        delivery = WebhookDelivery(
            webhook_id=webhook.id,
            event_type=event_type,
            payload=payload,
            status="pending",
            tenant_id=webhook.tenant_id,
            created_at=datetime.now(UTC),
        )
        db.add(delivery)
        await db.commit()
        await db.refresh(delivery)
        return delivery

    @staticmethod
    async def send_webhook_delivery(
        delivery_id: str,
        webhook_url: str,
        payload: dict[str, Any],
        headers: dict[str, str],
        timeout: float = 30.0,
    ) -> dict[str, Any]:
        """
        Send webhook delivery with retry logic.
        Args:
            delivery_id: Delivery record ID
            webhook_url: Webhook URL
            payload: Payload to send
            headers: Headers to include
            timeout: Request timeout
        Returns:
            Delivery result
        """
        from manushya.db.database import get_db

        async with get_db() as db:
            # Get delivery record
            stmt = select(WebhookDelivery).where(WebhookDelivery.id == delivery_id)
            result = await db.execute(stmt)
            delivery = result.scalar_one_or_none()
            if not delivery:
                logger.error(f"Delivery record {delivery_id} not found")
                return {"success": False, "error": "Delivery record not found"}
            # Validate URL
            try:
                parsed_url = urlparse(webhook_url)
                if not parsed_url.scheme or not parsed_url.netloc:
                    raise ValueError("Invalid URL")
            except Exception as e:
                await WebhookService._mark_delivery_failed(
                    db, delivery, f"Invalid URL: {str(e)}"
                )
                return {"success": False, "error": f"Invalid URL: {str(e)}"}
            # Send with retry logic
            return await WebhookService._send_with_retry(
                db, delivery, webhook_url, payload, headers, timeout
            )

    @staticmethod
    async def _send_with_retry(
        db: AsyncSession,
        delivery: WebhookDelivery,
        webhook_url: str,
        payload: dict[str, Any],
        headers: dict[str, str],
        timeout: float,
    ) -> dict[str, Any]:
        """Send webhook with exponential backoff retry logic."""
        # Add default headers
        default_headers = {
            "Content-Type": "application/json",
            "User-Agent": "Manushya-Webhook/1.0",
            "X-Webhook-Event": delivery.event_type,
            "X-Webhook-Delivery": str(delivery.id),
        }
        headers.update(default_headers)
        delay = WEBHOOK_CONFIG["initial_delay"]
        last_error = None
        for attempt in range(WEBHOOK_CONFIG["max_retries"] + 1):
            try:
                # Update delivery status
                delivery.status = "sending"
                delivery.attempts = attempt + 1
                delivery.last_attempt_at = datetime.now(UTC)
                await db.commit()
                # Send request
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.post(
                        webhook_url, json=payload, headers=headers
                    )
                # Check response
                if 200 <= response.status_code < 300:
                    # Success
                    await WebhookService._mark_delivery_success(
                        db, delivery, response.status_code, response.text
                    )
                    logger.info(
                        f"Webhook delivery {delivery.id} successful on attempt {attempt + 1}"
                    )
                    return {
                        "success": True,
                        "status_code": response.status_code,
                        "response": response.text,
                    }
                else:
                    # HTTP error
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                    last_error = error_msg
                    logger.warning(
                        f"Webhook delivery {delivery.id} failed with {error_msg}"
                    )
            except httpx.TimeoutException:
                error_msg = f"Timeout after {timeout}s"
                last_error = error_msg
                logger.warning(
                    f"Webhook delivery {delivery.id} timeout on attempt {attempt + 1}"
                )
            except httpx.RequestError as e:
                error_msg = f"Request error: {str(e)}"
                last_error = error_msg
                logger.warning(
                    f"Webhook delivery {delivery.id} request error on attempt {attempt + 1}: {e}"
                )
            except Exception as e:
                error_msg = f"Unexpected error: {str(e)}"
                last_error = error_msg
                logger.error(
                    f"Webhook delivery {delivery.id} unexpected error on attempt {attempt + 1}: {e}"
                )
            # If this was the last attempt, mark as failed
            if attempt == WEBHOOK_CONFIG["max_retries"]:
                await WebhookService._mark_delivery_failed(db, delivery, last_error)
                return {"success": False, "error": last_error}
            # Wait before retry
            await asyncio.sleep(delay)
            delay = min(
                delay * WEBHOOK_CONFIG["backoff_factor"], WEBHOOK_CONFIG["max_delay"]
            )
        return {"success": False, "error": "Max retries exceeded"}

    @staticmethod
    async def _mark_delivery_success(
        db: AsyncSession,
        delivery: WebhookDelivery,
        status_code: int,
        response_text: str,
    ):
        """Mark delivery as successful."""
        delivery.status = "delivered"
        delivery.status_code = status_code
        delivery.response_body = response_text
        delivery.delivered_at = datetime.now(UTC)
        await db.commit()

    @staticmethod
    async def _mark_delivery_failed(
        db: AsyncSession, delivery: WebhookDelivery, error_message: str
    ):
        """Mark delivery as failed."""
        delivery.status = "failed"
        delivery.error_message = error_message
        delivery.failed_at = datetime.now(UTC)
        await db.commit()

    @staticmethod
    async def get_delivery_stats(
        db: AsyncSession, tenant_id: str, days: int = 30
    ) -> dict[str, Any]:
        """Get webhook delivery statistics."""
        since = datetime.now(UTC) - timedelta(days=days)
        # Get delivery counts by status
        stmt = select(WebhookDelivery).where(
            and_(
                WebhookDelivery.tenant_id == tenant_id,
                WebhookDelivery.created_at >= since,
            )
        )
        result = await db.execute(stmt)
        deliveries = result.scalars().all()
        stats = {
            "total": len(deliveries),
            "delivered": len([d for d in deliveries if d.status == "delivered"]),
            "failed": len([d for d in deliveries if d.status == "failed"]),
            "pending": len([d for d in deliveries if d.status == "pending"]),
            "sending": len([d for d in deliveries if d.status == "sending"]),
            "success_rate": 0.0,
        }
        if stats["total"] > 0:
            stats["success_rate"] = stats["delivered"] / stats["total"]
        return stats

    @staticmethod
    async def cleanup_old_deliveries(db: AsyncSession, days: int = 90) -> int:
        """Clean up old webhook delivery records."""
        cutoff = datetime.now(UTC) - timedelta(days=days)
        stmt = select(WebhookDelivery).where(WebhookDelivery.created_at < cutoff)
        result = await db.execute(stmt)
        old_deliveries = result.scalars().all()
        deleted_count = 0
        for delivery in old_deliveries:
            await db.delete(delivery)
            deleted_count += 1
        if deleted_count > 0:
            await db.commit()
            logger.info(f"Cleaned up {deleted_count} old webhook delivery records")
        return deleted_count
