"""
Usage metering API endpoints for enterprise billing and analytics.
"""

from datetime import date, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from manushya.core.auth import get_current_identity
from manushya.db.database import get_db
from manushya.db.models import Identity
from manushya.services.usage_service import UsageService

router = APIRouter(prefix="/usage", tags=["usage"])


class UsageEventResponse(BaseModel):
    """Usage event response model."""

    id: str
    tenant_id: str
    api_key_id: str | None = None
    identity_id: str | None = None
    event: str
    units: int
    event_metadata: dict[str, Any]
    created_at: datetime


class UsageDailyResponse(BaseModel):
    """Daily usage response model."""

    id: str
    tenant_id: str
    date: date
    event: str
    units: int
    created_at: datetime
    updated_at: datetime


class UsageSummaryResponse(BaseModel):
    """Usage summary response model."""

    tenant_id: str
    period: dict[str, Any]
    totals: dict[str, int]
    daily_breakdown: list[dict[str, Any]]


@router.get("/events", response_model=list[UsageEventResponse])
async def get_usage_events(
    start_date: date | None = Query(None, description="Start date for filtering"),
    end_date: date | None = Query(None, description="End date for filtering"),
    event_type: str | None = Query(None, description="Filter by event type"),
    limit: int = Query(100, ge=1, le=1000, description="Number of events to return"),
    offset: int = Query(0, ge=0, description="Number of events to skip"),
    current_identity: Identity = Depends(get_current_identity),
    db=Depends(get_db),
):
    """Get usage events for the current tenant."""
    if not current_identity.tenant_id:
        raise HTTPException(status_code=403, detail="Tenant access required")
    usage_service = UsageService(db)
    events = usage_service.get_tenant_usage(
        tenant_id=current_identity.tenant_id,
        start_date=start_date,
        end_date=end_date,
        event_type=event_type,
    )
    # Apply pagination
    events = events[offset : offset + limit]
    return [
        UsageEventResponse(
            id=str(event.id),
            tenant_id=str(event.tenant_id),
            api_key_id=str(event.api_key_id) if event.api_key_id else None,
            identity_id=str(event.identity_id) if event.identity_id else None,
            event=event.event,
            units=event.units,
            event_metadata=event.event_metadata or {},
            created_at=event.created_at,
        )
        for event in events
    ]


@router.get("/daily", response_model=list[UsageDailyResponse])
async def get_daily_usage(
    start_date: date | None = Query(None, description="Start date for filtering"),
    end_date: date | None = Query(None, description="End date for filtering"),
    event_type: str | None = Query(None, description="Filter by event type"),
    current_identity: Identity = Depends(get_current_identity),
    db=Depends(get_db),
):
    """Get daily aggregated usage for the current tenant."""
    if not current_identity.tenant_id:
        raise HTTPException(status_code=403, detail="Tenant access required")
    usage_service = UsageService(db)
    daily_usage = usage_service.get_daily_usage(
        tenant_id=current_identity.tenant_id,
        start_date=start_date,
        end_date=end_date,
        event_type=event_type,
    )
    return [
        UsageDailyResponse(
            id=str(record.id),
            tenant_id=str(record.tenant_id),
            date=record.date,
            event=record.event,
            units=record.units,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )
        for record in daily_usage
    ]


@router.get("/summary", response_model=UsageSummaryResponse)
async def get_usage_summary(
    days: int = Query(30, ge=1, le=365, description="Number of days to summarize"),
    current_identity: Identity = Depends(get_current_identity),
    db=Depends(get_db),
):
    """Get usage summary for the current tenant."""
    if not current_identity.tenant_id:
        raise HTTPException(status_code=403, detail="Tenant access required")
    usage_service = UsageService(db)
    summary = usage_service.get_usage_summary(
        tenant_id=current_identity.tenant_id,
        days=days,
    )
    return UsageSummaryResponse(**summary)


@router.post("/aggregate")
async def trigger_usage_aggregation(
    target_date: date | None = Query(
        None, description="Target date for aggregation (defaults to today)"
    ),
    current_identity: Identity = Depends(get_current_identity),
    db=Depends(get_db),
):
    """Trigger manual usage aggregation (admin only)."""
    if current_identity.role not in ["admin", "it_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    usage_service = UsageService(db)
    updated_count = usage_service.aggregate_daily_usage(target_date=target_date)
    return {
        "message": f"Successfully aggregated {updated_count} daily usage records",
        "target_date": (
            target_date.isoformat() if target_date else date.today().isoformat()
        ),
        "updated_count": updated_count,
    }


@router.get("/admin/all-tenants", response_model=list[UsageSummaryResponse])
async def get_all_tenants_usage(
    start_date: date | None = Query(None, description="Start date for filtering"),
    end_date: date | None = Query(None, description="End date for filtering"),
    current_identity: Identity = Depends(get_current_identity),
    db=Depends(get_db),
):
    """Get usage summary for all tenants (admin only)."""
    if current_identity.role not in ["admin", "it_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    usage_service = UsageService(db)
    summaries = usage_service.get_all_tenants_usage(
        start_date=start_date,
        end_date=end_date,
    )
    return [UsageSummaryResponse(**summary) for summary in summaries]
