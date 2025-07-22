"""
Usage metering service for enterprise billing and analytics.
"""

import uuid
from datetime import UTC, date, datetime, timedelta
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from manushya.db.models import Tenant, UsageDaily, UsageEvent


class UsageService:
    """Service for tracking and aggregating usage metrics."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def track_event(
        self,
        tenant_id: uuid.UUID,
        event: str,
        units: int = 1,
        api_key_id: uuid.UUID | None = None,
        identity_id: uuid.UUID | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> UsageEvent:
        """Track a usage event for billing."""
        usage_event = UsageEvent(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            api_key_id=api_key_id,
            identity_id=identity_id,
            event=event,
            units=units,
            event_metadata=metadata or {},
        )
        self.db.add(usage_event)
        await self.db.commit()
        await self.db.refresh(usage_event)
        return usage_event

    def get_tenant_usage(
        self,
        tenant_id: uuid.UUID,
        start_date: date | None = None,
        end_date: date | None = None,
        event_type: str | None = None,
    ) -> list[UsageEvent]:
        """Get usage events for a tenant."""
        query = select(UsageEvent).where(UsageEvent.tenant_id == tenant_id)
        if start_date:
            query = query.where(UsageEvent.created_at >= start_date)
        if end_date:
            query = query.where(UsageEvent.created_at <= end_date)
        if event_type:
            query = query.where(UsageEvent.event == event_type)
        query = query.order_by(UsageEvent.created_at.desc())
        return list(self.db.execute(query).scalars().all())

    def get_daily_usage(
        self,
        tenant_id: uuid.UUID,
        start_date: date | None = None,
        end_date: date | None = None,
        event_type: str | None = None,
    ) -> list[UsageDaily]:
        """Get daily aggregated usage for a tenant."""
        query = select(UsageDaily).where(UsageDaily.tenant_id == tenant_id)
        if start_date:
            query = query.where(UsageDaily.date >= start_date)
        if end_date:
            query = query.where(UsageDaily.date <= end_date)
        if event_type:
            query = query.where(UsageDaily.event == event_type)
        query = query.order_by(UsageDaily.date.desc())
        return list(self.db.execute(query).scalars().all())

    def aggregate_daily_usage(self, target_date: date | None = None) -> int:
        """Aggregate usage events into daily totals."""
        if target_date is None:
            target_date = date.today()
        # Get all events for the target date
        start_datetime = datetime.combine(
            target_date, datetime.min.time(), tzinfo=UTC
        )
        end_datetime = datetime.combine(
            target_date, datetime.max.time(), tzinfo=UTC
        )
        # Aggregate events by tenant, date, and event type
        aggregation_query = (
            select(
                UsageEvent.tenant_id,
                func.date(UsageEvent.created_at).label("date"),
                UsageEvent.event,
                func.sum(UsageEvent.units).label("total_units"),
            )
            .where(
                and_(
                    UsageEvent.created_at >= start_datetime,
                    UsageEvent.created_at <= end_datetime,
                )
            )
            .group_by(
                UsageEvent.tenant_id, func.date(UsageEvent.created_at), UsageEvent.event
            )
        )
        results = self.db.execute(aggregation_query).all()
        # Update or create daily records
        updated_count = 0
        for result in results:
            daily_record = self.db.execute(
                select(UsageDaily).where(
                    and_(
                        UsageDaily.tenant_id == result.tenant_id,
                        UsageDaily.date == result.date,
                        UsageDaily.event == result.event,
                    )
                )
            ).scalar_one_or_none()
            if daily_record:
                daily_record.units = result.total_units
                daily_record.updated_at = datetime.now(UTC)
            else:
                daily_record = UsageDaily(
                    id=uuid.uuid4(),
                    tenant_id=result.tenant_id,
                    date=result.date,
                    event=result.event,
                    units=result.total_units,
                )
                self.db.add(daily_record)
            updated_count += 1
        self.db.commit()
        return updated_count

    def get_usage_summary(
        self,
        tenant_id: uuid.UUID,
        days: int = 30,
    ) -> dict[str, Any]:
        """Get usage summary for a tenant."""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        # Get daily usage for the period
        daily_usage = self.get_daily_usage(
            tenant_id=tenant_id, start_date=start_date, end_date=end_date
        )
        # Calculate totals by event type
        totals = {}
        for record in daily_usage:
            if record.event not in totals:
                totals[record.event] = 0
            totals[record.event] += record.units
        return {
            "tenant_id": str(tenant_id),
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days,
            },
            "totals": totals,
            "daily_breakdown": [
                {
                    "date": record.date.isoformat(),
                    "event": record.event,
                    "units": record.units,
                }
                for record in daily_usage
            ],
        }

    def get_all_tenants_usage(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[dict[str, Any]]:
        """Get usage summary for all tenants."""
        if start_date is None:
            start_date = date.today() - timedelta(days=30)
        if end_date is None:
            end_date = date.today()
        # Get all tenants
        tenants = list(self.db.execute(select(Tenant)).scalars().all())
        summaries = []
        for tenant in tenants:
            summary = self.get_usage_summary(
                tenant_id=tenant.id, days=(end_date - start_date).days
            )
            summaries.append(summary)
        return summaries
