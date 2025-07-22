"""
Background tasks for webhook delivery
"""

import asyncio

import structlog

from manushya.db.database import get_db
from manushya.services.webhook_service import WebhookService
from manushya.tasks.celery_app import celery_app

logger = structlog.get_logger()


@celery_app.task(bind=True, max_retries=3)
def deliver_webhook_task(self, delivery_id: str):
    """Background task to deliver a webhook."""
    try:
        # Run the async delivery function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def _deliver():
            async for db in get_db():
                # Get delivery record and send webhook
                from manushya.db.models import WebhookDelivery
                from sqlalchemy import select
                
                stmt = select(WebhookDelivery).where(WebhookDelivery.id == delivery_id)
                result = await db.execute(stmt)
                delivery = result.scalar_one_or_none()
                
                if not delivery:
                    logger.error(f"Delivery record {delivery_id} not found")
                    return False
                
                # Get webhook details
                webhook = delivery.webhook
                if not webhook:
                    logger.error(f"Webhook not found for delivery {delivery_id}")
                    return False
                
                # Send webhook
                result = await WebhookService.send_webhook_delivery(
                    delivery_id=delivery_id,
                    webhook_url=webhook.url,
                    payload=delivery.payload,
                    headers={},
                    timeout=30.0
                )
                return result.get("success", False)

        success = loop.run_until_complete(_deliver())
        loop.close()
        if not success:
            # Retry the task
            raise self.retry(countdown=60, max_retries=3)
        logger.info("Webhook delivered successfully", delivery_id=delivery_id)
        return success
    except Exception as e:
        logger.error("Webhook delivery failed", delivery_id=delivery_id, error=str(e))
        raise self.retry(countdown=60, max_retries=3) from e


@celery_app.task
def retry_failed_webhooks_task():
    """Background task to retry failed webhook deliveries."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def _retry():
            async for db in get_db():
                retry_count = await WebhookService.retry_failed_deliveries(db)
                return retry_count

        retry_count = loop.run_until_complete(_retry())
        loop.close()
        logger.info("Retried failed webhooks", retry_count=retry_count)
        return retry_count
    except Exception as e:
        logger.error("Failed to retry webhooks", error=str(e))
        return 0


@celery_app.task
def cleanup_old_webhooks_task(days_old: int = 30):
    """Background task to cleanup old webhook deliveries."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def _cleanup():
            async for db in get_db():
                cleaned_count = await WebhookService.cleanup_old_deliveries(
                    db, days_old
                )
                return cleaned_count

        cleaned_count = loop.run_until_complete(_cleanup())
        loop.close()
        logger.info("Cleaned up old webhook deliveries", cleaned_count=cleaned_count)
        return cleaned_count
    except Exception as e:
        logger.error("Failed to cleanup webhooks", error=str(e))
        return 0
