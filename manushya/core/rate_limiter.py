"""
Rate limiting service for Manushya.ai
"""

import time
from datetime import datetime, timedelta
from typing import cast

import structlog
from fastapi import HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from manushya.config import settings
from manushya.core.redis_client import get_redis
from manushya.db.models import Identity, RateLimit
from manushya.services.webhook_service import WebhookService

logger = structlog.get_logger()
# Redis client for primary rate limiting
_redis_client = None


def get_redis_client():
    """Get Redis client with lazy initialization."""
    global _redis_client
    if _redis_client is None:
        try:
            import redis.asyncio as redis

            _redis_client = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                db=settings.redis_db,
                decode_responses=True,
            )
        except ImportError:
            logger.warning("Redis not available, using database fallback")
            _redis_client = None
    return _redis_client


class RateLimiter:
    """Rate limiting service for API endpoints."""

    # Default rate limits (requests per window)
    DEFAULT_LIMITS: dict[str, dict[str, int]] = {
        "identity": {"window": 60, "limit": 100},  # 100 requests per minute
        "memory": {"window": 60, "limit": 200},  # 200 requests per minute
        "policy": {"window": 60, "limit": 50},  # 50 requests per minute
        "api_keys": {"window": 60, "limit": 30},  # 30 requests per minute
        "invitations": {"window": 60, "limit": 20},  # 20 requests per minute
        "sessions": {"window": 60, "limit": 100},  # 100 requests per minute
        "events": {"window": 60, "limit": 50},  # 50 requests per minute
        "default": {"window": 60, "limit": 100},  # Default limit
    }
    # Role-based limits (multipliers)
    ROLE_LIMITS = {
        "admin": 2.0,  # Admins get 2x the limit
        "system": 5.0,  # System gets 5x the limit
        "default": 1.0,  # Default multiplier
    }

    @staticmethod
    def get_client_key(request: Request, identity: Identity | None = None) -> str:
        """Generate a unique key for rate limiting."""
        if identity:
            # Use identity ID for authenticated requests
            return f"identity:{identity.id}"
        else:
            # Use IP address for unauthenticated requests
            client_ip = request.client.host if request.client else "unknown"
            return f"ip:{client_ip}"

    @staticmethod
    def get_endpoint_key(endpoint: str) -> str:
        """Get the rate limit key for an endpoint. Always returns a str."""
        if endpoint and isinstance(endpoint, str):
            if endpoint.startswith("/v1/identity"):
                return "identity"
            elif endpoint.startswith("/v1/memory"):
                return "memory"
            elif endpoint.startswith("/v1/policy"):
                return "policy"
            elif endpoint.startswith("/v1/api-keys"):
                return "api_keys"
            elif endpoint.startswith("/v1/invitations"):
                return "invitations"
            elif endpoint.startswith("/v1/sessions"):
                return "sessions"
            elif endpoint.startswith("/v1/events"):
                return "events"
        return "default"

    @staticmethod
    def calculate_limit(
        base_limit: int, role: str | None = None, tenant_id: str | None = None
    ) -> int:
        """Calculate the actual limit based on role and tenant."""
        # Apply role multiplier
        role_key = role if role is not None else "default"
        role_multiplier = RateLimiter.ROLE_LIMITS.get(
            role_key, RateLimiter.ROLE_LIMITS["default"]
        )
        limit = int(base_limit * role_multiplier)
        # In production, you could apply tenant-specific limits here
        # if tenant_id:
        #     tenant_limit = get_tenant_rate_limit(tenant_id)
        #     limit = min(limit, tenant_limit)
        return limit

    @staticmethod
    async def check_rate_limit(
        request: Request,
        db: AsyncSession,
        identity: Identity | None = None,
        endpoint: str | None = None,
    ) -> tuple[bool, dict]:
        """Check if the request is within rate limits."""
        if not endpoint:
            endpoint = request.url.path
        endpoint_key = RateLimiter.get_endpoint_key(endpoint)
        endpoint_key = cast(str, endpoint_key)
        client_key = RateLimiter.get_client_key(request, identity)
        # Get rate limit configuration
        if endpoint_key in RateLimiter.DEFAULT_LIMITS:
            limit_config = RateLimiter.DEFAULT_LIMITS[endpoint_key]
        else:
            limit_config = RateLimiter.DEFAULT_LIMITS["default"]
        window_seconds = limit_config["window"]
        base_limit = limit_config["limit"]
        # Calculate actual limit based on role
        role = identity.role if identity else "anonymous"
        tenant_id = str(identity.tenant_id) if identity and identity.tenant_id else None
        actual_limit = RateLimiter.calculate_limit(base_limit, role, tenant_id)
        # Try Redis first
        try:
            redis = await get_redis()
            redis_key = f"ratelimit:{client_key}:{endpoint_key}"
            count = await redis.incr(redis_key)
            if count == 1:
                await redis.expire(redis_key, window_seconds)
            if count > actual_limit:
                return False, {
                    "limit": actual_limit,
                    "remaining": 0,
                    "reset_time": int(time.time()) + window_seconds,
                    "window_seconds": window_seconds,
                }
            remaining = max(0, actual_limit - count)
            return True, {
                "limit": actual_limit,
                "remaining": remaining,
                "reset_time": int(time.time()) + window_seconds,
                "window_seconds": window_seconds,
            }
        except Exception as e:
            logger.warning("Redis unavailable, falling back to DB", error=str(e))
        # Get current timestamp
        current_time = datetime.utcnow()
        window_start = current_time - timedelta(seconds=window_seconds)
        # Check existing rate limit records
        stmt = select(RateLimit).where(
            RateLimit.client_key == client_key,
            RateLimit.endpoint == endpoint_key,
            RateLimit.window_start >= window_start,
        )
        result = await db.execute(stmt)
        rate_limit = result.scalar_one_or_none()
        if rate_limit:
            # Update existing record
            rate_limit.request_count += 1
            rate_limit.last_request_at = current_time
            await db.commit()
            # Check if limit exceeded
            if rate_limit.request_count > actual_limit:
                logger.warning(
                    "Rate limit exceeded",
                    client_key=client_key,
                    endpoint=endpoint_key,
                    request_count=rate_limit.request_count,
                    limit=actual_limit,
                    window_seconds=window_seconds,
                )
                # Trigger webhook for rate limit exceeded
                try:
                    await WebhookService.trigger_webhook(
                        db=db,
                        event_type="rate_limit.exceeded",
                        payload={
                            "client_key": client_key,
                            "endpoint": endpoint_key,
                            "request_count": rate_limit.request_count,
                            "limit": actual_limit,
                            "window_seconds": window_seconds,
                            "identity_id": str(identity.id) if identity else None,
                            "tenant_id": str(identity.tenant_id) if identity else None,
                            "exceeded_at": datetime.utcnow().isoformat(),
                        },
                        tenant_id=str(identity.tenant_id) if identity else None,
                    )
                except Exception as e:
                    logger.error("Failed to trigger rate limit webhook", error=str(e))
                return False, {
                    "limit": actual_limit,
                    "remaining": 0,
                    "reset_time": (
                        rate_limit.window_start + timedelta(seconds=window_seconds)
                    ).timestamp(),
                    "window_seconds": window_seconds,
                }
            remaining = max(0, actual_limit - rate_limit.request_count)
            return True, {
                "limit": actual_limit,
                "remaining": remaining,
                "reset_time": (
                    rate_limit.window_start + timedelta(seconds=window_seconds)
                ).timestamp(),
                "window_seconds": window_seconds,
            }
        else:
            # Create new rate limit record
            rate_limit = RateLimit(
                client_key=client_key,
                endpoint=endpoint_key,
                window_start=window_start,
                request_count=1,
                last_request_at=current_time,
                tenant_id=identity.tenant_id if identity else None,
            )
            db.add(rate_limit)
            await db.commit()
            remaining = max(0, actual_limit - 1)
            return True, {
                "limit": actual_limit,
                "remaining": remaining,
                "reset_time": (
                    window_start + timedelta(seconds=window_seconds)
                ).timestamp(),
                "window_seconds": window_seconds,
            }

    @staticmethod
    async def get_rate_limit_info(
        request: Request,
        db: AsyncSession,
        identity: Identity | None = None,
        endpoint: str | None = None,
    ) -> dict:
        """Get current rate limit information without incrementing the counter."""
        if not endpoint:
            endpoint = request.url.path
        endpoint_key = RateLimiter.get_endpoint_key(endpoint)
        endpoint_key = cast(str, endpoint_key)
        client_key = RateLimiter.get_client_key(request, identity)
        # Get rate limit configuration
        if endpoint_key in RateLimiter.DEFAULT_LIMITS:
            limit_config = RateLimiter.DEFAULT_LIMITS[endpoint_key]
        else:
            limit_config = RateLimiter.DEFAULT_LIMITS["default"]
        window_seconds = limit_config["window"]
        base_limit = limit_config["limit"]
        # Calculate actual limit based on role
        role = identity.role if identity else "anonymous"
        tenant_id = str(identity.tenant_id) if identity and identity.tenant_id else None
        actual_limit = RateLimiter.calculate_limit(base_limit, role, tenant_id)
        # Get current timestamp
        current_time = datetime.utcnow()
        window_start = current_time - timedelta(seconds=window_seconds)
        # Check existing rate limit records
        stmt = select(RateLimit).where(
            RateLimit.client_key == client_key,
            RateLimit.endpoint == endpoint_key,
            RateLimit.window_start >= window_start,
        )
        result = await db.execute(stmt)
        rate_limit = result.scalar_one_or_none()
        if rate_limit:
            request_count = rate_limit.request_count
        else:
            request_count = 0
        remaining = max(0, actual_limit - request_count)
        return {
            "limit": actual_limit,
            "remaining": remaining,
            "used": request_count,
            "reset_time": (
                window_start + timedelta(seconds=window_seconds)
            ).timestamp(),
            "window_seconds": window_seconds,
            "endpoint": endpoint_key,
            "client_key": client_key,
        }

    @staticmethod
    async def cleanup_expired_limits(db: AsyncSession, hours_old: int = 24) -> int:
        """Clean up expired rate limit records."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_old)
        stmt = select(RateLimit).where(RateLimit.window_start < cutoff_time)
        result = await db.execute(stmt)
        expired_limits = result.scalars().all()
        cleaned_count = 0
        for rate_limit in expired_limits:
            await db.delete(rate_limit)
            cleaned_count += 1
        await db.commit()
        logger.info(
            "Cleaned up expired rate limits",
            cleaned_count=cleaned_count,
            cutoff_time=cutoff_time.isoformat(),
        )
        return cleaned_count

    @staticmethod
    async def redis_health() -> bool:
        try:
            redis = await get_redis()
            await redis.ping()
            return True
        except Exception:
            return False


async def rate_limit_middleware(
    request: Request, db: AsyncSession, identity: Identity | None = None
) -> None:
    """Middleware to check rate limits."""
    try:
        allowed, limit_info = await RateLimiter.check_rate_limit(request, db, identity)
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Rate limit exceeded",
                    "limit": limit_info["limit"],
                    "reset_time": limit_info["reset_time"],
                    "window_seconds": limit_info["window_seconds"],
                },
                headers={
                    "X-RateLimit-Limit": str(limit_info["limit"]),
                    "X-RateLimit-Remaining": str(limit_info["remaining"]),
                    "X-RateLimit-Reset": str(int(limit_info["reset_time"])),
                    "Retry-After": str(limit_info["window_seconds"]),
                },
            )
        # Add rate limit headers to response
        request.state.rate_limit_info = limit_info
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Rate limiting error", error=str(e))
        # Don't block the request if rate limiting fails


# Global rate limit configurations
RATE_LIMITS = {
    "identity:create": {"limit": 10, "window": 3600},  # 10 per hour
    "identity:login": {"limit": 20, "window": 3600},  # 20 per hour
    "memory:create": {"limit": 100, "window": 3600},  # 100 per hour
    "memory:search": {"limit": 200, "window": 3600},  # 200 per hour
    "api_key:create": {"limit": 5, "window": 3600},  # 5 per hour
    "webhook:create": {"limit": 20, "window": 3600},  # 20 per hour
    "invitation:create": {"limit": 50, "window": 3600},  # 50 per hour
    "default": {"limit": 1000, "window": 3600},  # 1000 per hour
}


def get_rate_limit_config(key: str) -> dict:
    """Get rate limit configuration for a key."""
    return RATE_LIMITS.get(key, RATE_LIMITS["default"])


async def check_rate_limit_middleware(
    request_key: str,
    db: AsyncSession,
    identity_id: str | None = None,
    tenant_id: str | None = None,
) -> tuple[bool, dict]:
    """Middleware function to check rate limits."""
    limiter = RateLimiter(db)
    config = get_rate_limit_config(request_key)
    allowed, info = await limiter.check_rate_limit(
        key=request_key,
        limit=config["limit"],
        window_seconds=config["window"],
        identity_id=identity_id,
        tenant_id=tenant_id,
    )
    if not allowed:
        logger.warning(f"Rate limit exceeded for {request_key}: {info}")
    return allowed, info
