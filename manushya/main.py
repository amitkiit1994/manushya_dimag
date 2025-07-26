"""
Main FastAPI application for Manushya.ai
"""

import asyncio
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

import structlog
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from sqlalchemy.exc import SQLAlchemyError
from starlette.middleware.sessions import SessionMiddleware

# Import routers after they're created
from manushya.api.v1 import (
    api_keys,
    events,
    identity,
    invitations,
    memory,
    monitoring,
    policy,
    sessions,
    sso,
    usage,
    webhooks,
)
from manushya.api.v1.policy import admin_router, monitoring_router
from manushya.config import settings
from manushya.core.auth import get_optional_identity
from manushya.core.exceptions import ErrorHandler, ManushyaException
from manushya.core.rate_limiter import RateLimiter, rate_limit_middleware
from manushya.core.redis_client import close_redis, get_redis
from manushya.db.database import check_db_health, close_db, get_db, init_db

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)
logger = structlog.get_logger()
# Prometheus metrics
REQUEST_COUNT = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"]
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds", "HTTP request latency", ["method", "endpoint"]
)


# Redis connection
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Manushya.ai application", version=settings.version)
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
        raise
    await get_redis()
    # Optionally: start background cleanup task
    asyncio.create_task(background_cleanup_jobs())
    yield
    # Shutdown
    logger.info("Shutting down Manushya.ai application")
    await close_redis()
    await close_db()


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="Secure identity + memory infrastructure for autonomous AI agents",
    docs_url="/v1/docs" if settings.debug else None,
    redoc_url="/v1/redoc" if settings.debug else None,
    openapi_url="/v1/openapi.json" if settings.debug else None,
    root_path=settings.root_path,
    lifespan=lifespan,
)
# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods_list,
    allow_headers=settings.cors_allow_headers_list,
)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"] if settings.debug else settings.allowed_hosts_list,
)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.jwt_secret_key,
    max_age=3600,  # 1 hour
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time header and log requests."""
    start_time = time.time()
    # Generate request ID
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    # Log request
    logger.info(
        "HTTP request started",
        request_id=request_id,
        method=request.method,
        url=str(request.url),
        client_ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    response = await call_next(request)
    # Calculate processing time
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    response.headers["X-Request-ID"] = request_id
    # Update metrics
    REQUEST_COUNT.labels(
        method=request.method, endpoint=request.url.path, status=response.status_code
    ).inc()
    REQUEST_LATENCY.labels(method=request.method, endpoint=request.url.path).observe(
        process_time
    )
    # Log response
    logger.info(
        "HTTP request completed",
        request_id=request_id,
        method=request.method,
        url=str(request.url),
        status_code=response.status_code,
        process_time=process_time,
    )
    return response


@app.middleware("http")
async def rate_limiting_http_middleware(request: Request, call_next):
    # Skip rate limiting for health, metrics, and docs
    if request.url.path in [
        "/healthz",
        "/metrics",
        "/v1/docs",
        "/v1/openapi.json",
        "/v1/redoc",
    ]:
        return await call_next(request)
    # Get DB session
    async for db in get_db():
        # Get identity (if any)
        identity = await get_optional_identity(request, db)
        # Run rate limiting check
        await rate_limit_middleware(request, db, identity)
        break
    response = await call_next(request)
    # Add rate limit headers if available
    limit_info = getattr(request.state, "rate_limit_info", None)
    if limit_info:
        response.headers["X-RateLimit-Limit"] = str(limit_info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(limit_info["remaining"])
        response.headers["X-RateLimit-Reset"] = str(int(limit_info["reset_time"]))
        response.headers["Retry-After"] = str(limit_info["window_seconds"])
    return response


# Exception handlers
@app.exception_handler(ManushyaException)
async def manushya_exception_handler(request: Request, exc: ManushyaException):
    """Handle custom Manushya exceptions."""
    logger.error(
        "Manushya exception",
        request_id=getattr(request.state, "request_id", None),
        error=exc.message,
        error_code=exc.error_code,
        details=exc.details,
    )
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": exc.message,
            "error_code": exc.error_code,
            "details": exc.details,
            "request_id": getattr(request.state, "request_id", None),
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    logger.error(
        "Validation error",
        request_id=getattr(request.state, "request_id", None),
        errors=exc.errors(),
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation error",
            "details": exc.errors(),
            "request_id": getattr(request.state, "request_id", None),
        },
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """Handle SQLAlchemy database errors."""
    logger.error(
        "Database error",
        request_id=getattr(request.state, "request_id", None),
        error=str(exc),
        exc_info=True,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Database operation failed",
            "details": "A database error occurred while processing your request",
            "request_id": getattr(request.state, "request_id", None),
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return await ErrorHandler.handle_exception(request, exc)


@app.on_event("startup")
async def startup_event():
    await get_redis()
    # Optionally: start background cleanup task
    asyncio.create_task(background_cleanup_jobs())


async def background_cleanup_jobs():
    while True:
        try:
            async for db in get_db():
                await RateLimiter.cleanup_expired_limits(db)
                # Retry failed webhook deliveries
                from manushya.services.webhook_service import WebhookService

                WebhookService(db)
                # Note: Retry logic is now handled by Celery tasks
                # Clean up old webhook deliveries (weekly)
                if datetime.utcnow().weekday() == 0:  # Monday
                    await WebhookService.cleanup_old_deliveries(db)
                break
            # Add more cleanup jobs as needed
        except Exception as e:
            logger.error("Background cleanup error", error=str(e))
        await asyncio.sleep(3600)  # Run every hour


# Health check endpoint
@app.get("/healthz")
async def health_check() -> dict[str, Any]:
    db_ok = await check_db_health()
    redis_ok = False
    try:
        r = await get_redis()
        await r.ping()
        redis_ok = True
    except Exception:
        redis_ok = False
    return {
        "database": db_ok,
        "redis": redis_ok,
        "status": "ok" if db_ok and redis_ok else "degraded",
    }


# Metrics endpoint
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


# Include API routers
app.include_router(identity.router, prefix="/v1/identity", tags=["identity"])
app.include_router(memory.router, prefix="/v1/memory", tags=["memory"])
app.include_router(policy.router, prefix="/v1/policy", tags=["policy"])
app.include_router(api_keys.router, prefix="/v1/api-keys", tags=["api-keys"])
app.include_router(invitations.router, prefix="/v1/invitations", tags=["invitations"])
app.include_router(sessions.router, prefix="/v1/sessions", tags=["sessions"])
app.include_router(events.router, prefix="/v1/events", tags=["events"])
app.include_router(sso.router, prefix="/v1/sso", tags=["sso"])
app.include_router(admin_router)
app.include_router(monitoring_router)
app.include_router(monitoring.router, prefix="/v1/monitoring", tags=["monitoring"])
app.include_router(webhooks.router)
app.include_router(usage.router, prefix="/v1/usage", tags=["usage"])


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to Manushya.ai",
        "version": settings.version,
        "docs": "/v1/docs" if settings.debug else None,
        "health": "/healthz",
        "metrics": "/metrics",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "manushya.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
