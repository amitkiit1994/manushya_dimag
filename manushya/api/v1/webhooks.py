"""
Webhook API endpoints for real-time notifications
"""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy.ext.asyncio import AsyncSession

from manushya.core.auth import get_current_identity
from manushya.db.database import get_db
from manushya.db.models import Identity, Webhook, WebhookDelivery
from manushya.services.webhook_service import WebhookService

router = APIRouter(prefix="/v1/webhooks", tags=["webhooks"])


# Pydantic models
class WebhookCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Webhook name")
    url: HttpUrl = Field(..., description="Webhook URL")
    events: list[str] = Field(..., description="List of events to subscribe to")

class WebhookUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255, description="Webhook name")
    url: HttpUrl | None = Field(None, description="Webhook URL")
    events: list[str] | None = Field(None, description="List of events to subscribe to")
    is_active: bool | None = Field(None, description="Whether webhook is active")

class WebhookResponse(BaseModel):
    id: UUID
    name: str
    url: str
    events: list[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    tenant_id: UUID | None = None

class WebhookDeliveryResponse(BaseModel):
    id: UUID
    webhook_id: UUID
    event_type: str
    status: str
    response_code: int | None = None
    delivery_attempts: int
    next_retry_at: datetime | None = None
    delivered_at: datetime | None = None
    created_at: datetime

class WebhookStatsResponse(BaseModel):
    total_webhooks: int
    active_webhooks: int
    pending_deliveries: int
    failed_deliveries: int
    successful_deliveries: int


@router.post("/", response_model=WebhookResponse, status_code=status.HTTP_201_CREATED)
async def create_webhook(
    webhook_data: WebhookCreate,
    db: AsyncSession = Depends(get_db),
    identity: Identity = Depends(get_current_identity)
):
    """Create a new webhook registration."""
    try:
        webhook = await WebhookService.create_webhook(
            db=db,
            name=webhook_data.name,
            url=str(webhook_data.url),
            events=webhook_data.events,
            created_by=str(identity.id),
            tenant_id=str(identity.tenant_id) if identity.tenant_id else None
        )

        return WebhookResponse(
            id=webhook.id,
            name=webhook.name,
            url=webhook.url,
            events=webhook.events,
            is_active=webhook.is_active,
            created_at=webhook.created_at,
            updated_at=webhook.updated_at,
            tenant_id=webhook.tenant_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create webhook: {str(e)}") from e


@router.get("/", response_model=list[WebhookResponse])
async def list_webhooks(
    is_active: bool | None = None,
    db: AsyncSession = Depends(get_db),
    identity: Identity = Depends(get_current_identity)
):
    """List webhooks for the current tenant."""
    webhooks = await WebhookService.get_webhooks(
        db=db,
        tenant_id=str(identity.tenant_id) if identity.tenant_id else None,
        is_active=is_active
    )

    return [
        WebhookResponse(
            id=webhook.id,
            name=webhook.name,
            url=webhook.url,
            events=webhook.events,
            is_active=webhook.is_active,
            created_at=webhook.created_at,
            updated_at=webhook.updated_at,
            tenant_id=webhook.tenant_id
        )
        for webhook in webhooks
    ]


@router.get("/{webhook_id}", response_model=WebhookResponse)
async def get_webhook(
    webhook_id: UUID,
    db: AsyncSession = Depends(get_db),
    identity: Identity = Depends(get_current_identity)
):
    """Get a specific webhook by ID."""
    webhook = await WebhookService.get_webhook(db, str(webhook_id))

    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    # Check tenant access
    if identity.tenant_id and webhook.tenant_id != identity.tenant_id:
        raise HTTPException(status_code=403, detail="Access denied")

    return WebhookResponse(
        id=webhook.id,
        name=webhook.name,
        url=webhook.url,
        events=webhook.events,
        is_active=webhook.is_active,
        created_at=webhook.created_at,
        updated_at=webhook.updated_at,
        tenant_id=webhook.tenant_id
    )


@router.put("/{webhook_id}", response_model=WebhookResponse)
async def update_webhook(
    webhook_id: UUID,
    webhook_data: WebhookUpdate,
    db: AsyncSession = Depends(get_db),
    identity: Identity = Depends(get_current_identity)
):
    """Update a webhook."""
    # Check if webhook exists and user has access
    existing_webhook = await WebhookService.get_webhook(db, str(webhook_id))
    if not existing_webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    if identity.tenant_id and existing_webhook.tenant_id != identity.tenant_id:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        webhook = await WebhookService.update_webhook(
            db=db,
            webhook_id=str(webhook_id),
            name=webhook_data.name,
            url=str(webhook_data.url) if webhook_data.url else None,
            events=webhook_data.events,
            is_active=webhook_data.is_active
        )

        if not webhook:
            raise HTTPException(status_code=404, detail="Webhook not found")

        return WebhookResponse(
            id=webhook.id,
            name=webhook.name,
            url=webhook.url,
            events=webhook.events,
            is_active=webhook.is_active,
            created_at=webhook.created_at,
            updated_at=webhook.updated_at,
            tenant_id=webhook.tenant_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update webhook: {str(e)}") from e


@router.delete("/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook(
    webhook_id: UUID,
    db: AsyncSession = Depends(get_db),
    identity: Identity = Depends(get_current_identity)
):
    """Delete a webhook."""
    # Check if webhook exists and user has access
    existing_webhook = await WebhookService.get_webhook(db, str(webhook_id))
    if not existing_webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    if identity.tenant_id and existing_webhook.tenant_id != identity.tenant_id:
        raise HTTPException(status_code=403, detail="Access denied")

    success = await WebhookService.delete_webhook(db, str(webhook_id))
    if not success:
        raise HTTPException(status_code=404, detail="Webhook not found")


@router.get("/{webhook_id}/deliveries", response_model=list[WebhookDeliveryResponse])
async def list_webhook_deliveries(
    webhook_id: UUID,
    status_filter: str | None = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    identity: Identity = Depends(get_current_identity)
):
    """List deliveries for a specific webhook."""
    # Check if webhook exists and user has access
    webhook = await WebhookService.get_webhook(db, str(webhook_id))
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    if identity.tenant_id and webhook.tenant_id != identity.tenant_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Build query
    from sqlalchemy import select
    stmt = select(WebhookDelivery).where(WebhookDelivery.webhook_id == webhook_id)

    if status_filter:
        stmt = stmt.where(WebhookDelivery.status == status_filter)

    stmt = stmt.order_by(WebhookDelivery.created_at.desc()).limit(limit).offset(offset)

    result = await db.execute(stmt)
    deliveries = result.scalars().all()

    return [
        WebhookDeliveryResponse(
            id=delivery.id,
            webhook_id=delivery.webhook_id,
            event_type=delivery.event_type,
            status=delivery.status,
            response_code=delivery.response_code,
            delivery_attempts=delivery.delivery_attempts,
            next_retry_at=delivery.next_retry_at,
            delivered_at=delivery.delivered_at,
            created_at=delivery.created_at
        )
        for delivery in deliveries
    ]


@router.post("/{webhook_id}/deliveries/{delivery_id}/retry", status_code=status.HTTP_200_OK)
async def retry_webhook_delivery(
    webhook_id: UUID,
    delivery_id: UUID,
    db: AsyncSession = Depends(get_db),
    identity: Identity = Depends(get_current_identity)
):
    """Retry a failed webhook delivery."""
    # Check if webhook exists and user has access
    webhook = await WebhookService.get_webhook(db, str(webhook_id))
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    if identity.tenant_id and webhook.tenant_id != identity.tenant_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Check if delivery exists
    from sqlalchemy import select
    stmt = select(WebhookDelivery).where(
        WebhookDelivery.id == delivery_id,
        WebhookDelivery.webhook_id == webhook_id
    )
    result = await db.execute(stmt)
    delivery = result.scalar_one_or_none()

    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found")

    # Retry delivery
    success = await WebhookService.deliver_webhook(str(delivery_id), db)

    return {
        "success": success,
        "message": "Webhook delivery retry initiated" if success else "Webhook delivery retry failed"
    }


@router.get("/stats", response_model=WebhookStatsResponse)
async def get_webhook_stats(
    db: AsyncSession = Depends(get_db),
    identity: Identity = Depends(get_current_identity)
):
    """Get webhook statistics for the current tenant."""
    from sqlalchemy import func, select

    tenant_id = str(identity.tenant_id) if identity.tenant_id else None

    # Count webhooks
    webhook_stmt = select(func.count(Webhook.id)).where(Webhook.tenant_id == tenant_id)
    result = await db.execute(webhook_stmt)
    total_webhooks = result.scalar()

    active_webhook_stmt = select(func.count(Webhook.id)).where(
        Webhook.tenant_id == tenant_id,
        Webhook.is_active
    )
    result = await db.execute(active_webhook_stmt)
    active_webhooks = result.scalar()

    # Count deliveries by status
    delivery_stmt = select(
        WebhookDelivery.status,
        func.count(WebhookDelivery.id)
    ).join(Webhook).where(Webhook.tenant_id == tenant_id).group_by(WebhookDelivery.status)

    result = await db.execute(delivery_stmt)
    delivery_counts = {row[0]: row[1] for row in result.all()}

    return WebhookStatsResponse(
        total_webhooks=total_webhooks or 0,
        active_webhooks=active_webhooks or 0,
        pending_deliveries=delivery_counts.get("pending", 0) or 0,
        failed_deliveries=delivery_counts.get("failed", 0) or 0,
        successful_deliveries=delivery_counts.get("delivered", 0) or 0
    )


@router.get("/events", response_model=list[str])
async def get_supported_events():
    """Get list of supported webhook events."""
    return WebhookService.SUPPORTED_EVENTS
