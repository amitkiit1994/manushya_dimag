"""
Production-grade Celery configuration with advanced task management
"""

from datetime import timedelta
from typing import Any

from celery import Celery
from celery.schedules import crontab
from celery.signals import task_postrun, task_failure
from celery.utils.log import get_task_logger

from manushya.config import settings

logger = get_task_logger(__name__)
# Create Celery app
celery_app = Celery(
    "manushya",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "manushya.tasks.memory_tasks",
        "manushya.tasks.webhook_tasks",
        "manushya.tasks.cleanup_tasks",
        "manushya.tasks.monitoring_tasks",
    ],
)
# Production configuration
celery_app.conf.update(
    # Task serialization
    task_serializer=settings.celery_task_serializer,
    result_serializer=settings.celery_result_serializer,
    accept_content=settings.celery_accept_content_list,
    # Task routing and queues
    task_routes={
        "manushya.tasks.memory_tasks.*": {"queue": "memory"},
        "manushya.tasks.webhook_tasks.*": {"queue": "webhooks"},
        "manushya.tasks.cleanup_tasks.*": {"queue": "cleanup"},
        "manushya.tasks.monitoring_tasks.*": {"queue": "monitoring"},
    },
    # Task execution settings
    task_always_eager=False,  # Set to True for testing
    task_eager_propagates=True,
    task_ignore_result=False,
    task_store_errors_even_if_ignored=True,
    # Worker settings
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    worker_disable_rate_limits=False,
    # Result backend settings
    result_expires=timedelta(days=7),
    result_persistent=True,
    # Task time limits
    task_soft_time_limit=300,  # 5 minutes
    task_time_limit=600,  # 10 minutes
    # Retry settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    # Beat schedule for periodic tasks
    beat_schedule={
        "cleanup-expired-sessions": {
            "task": "manushya.tasks.cleanup_tasks.cleanup_expired_sessions",
            "schedule": crontab(minute=0, hour="*/6"),  # Every 6 hours
        },
        "cleanup-old-memories": {
            "task": "manushya.tasks.cleanup_tasks.cleanup_expired_memories",
            "schedule": crontab(minute=0, hour=2),  # Daily at 2 AM
        },
        "retry-failed-webhooks": {
            "task": "manushya.tasks.webhook_tasks.retry_failed_webhook_deliveries",
            "schedule": crontab(minute="*/15"),  # Every 15 minutes
        },
        "cleanup-old-webhook-deliveries": {
            "task": "manushya.tasks.cleanup_tasks.cleanup_old_webhook_deliveries",
            "schedule": crontab(minute=0, hour=3),  # Daily at 3 AM
        },
        "generate-missing-embeddings": {
            "task": "manushya.tasks.memory_tasks.generate_missing_embeddings",
            "schedule": crontab(minute="*/30"),  # Every 30 minutes
        },
        "update-system-metrics": {
            "task": "manushya.tasks.monitoring_tasks.update_system_metrics",
            "schedule": crontab(minute="*/5"),  # Every 5 minutes
        },
        "cleanup-rate-limits": {
            "task": "manushya.tasks.cleanup_tasks.cleanup_expired_rate_limits",
            "schedule": crontab(minute=0, hour="*/2"),  # Every 2 hours
        },
    },
    # Security settings
    security_key=settings.secret_key,
    security_certificate=None,
    security_cert_store=None,
    # Logging
    worker_log_format="[%(asctime)s: %(levelname)s/%(processName)s] %(message)s",
    worker_task_log_format="[%(asctime)s: %(levelname)s/%(processName)s] [%(task_name)s(%(task_id)s)] %(message)s",
)


# Task error handling
@celery_app.task(bind=True)
def debug_task(self):
    """Debug task for testing."""
    logger.info(f"Request: {self.request!r}")


# Task monitoring and metrics
class TaskMetrics:
    """Task metrics collection for monitoring."""

    @staticmethod
    def task_started(task_name: str, task_id: str):
        """Log task start."""
        logger.info(f"Task started: {task_name} ({task_id})")

    @staticmethod
    def task_completed(task_name: str, task_id: str, duration: float):
        """Log task completion."""
        logger.info(f"Task completed: {task_name} ({task_id}) in {duration:.2f}s")

    @staticmethod
    def task_failed(task_name: str, task_id: str, error: str):
        """Log task failure."""
        logger.error(f"Task failed: {task_name} ({task_id}) - {error}")


# Task signal handlers
@task_postrun.connect
def task_postrun_handler(**kwargs):
    """Handle task post-run events."""
    task = kwargs.get('task')
    task_id = kwargs.get('task_id')
    state = kwargs.get('state')
    
    if task and task_id:
        if state == "SUCCESS":
            TaskMetrics.task_completed(task.name, str(task_id), 0.0)
        else:
            TaskMetrics.task_failed(task.name, str(task_id), str(kwargs.get('retval')))


@task_failure.connect
def task_failure_handler(**kwargs):
    """Handle task failure events."""
    sender = kwargs.get('sender')
    task_id = kwargs.get('task_id')
    exception = kwargs.get('exception')
    
    if sender and task_id:
        TaskMetrics.task_failed(sender.name, str(task_id), str(exception))


# Health check task
@celery_app.task(bind=True)
def health_check(self):
    """Health check task for monitoring."""
    try:
        # Basic health checks
        import psutil
        import redis.asyncio as redis

        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        # Redis connectivity
        redis_client = redis.Redis.from_url(settings.redis_url)
        redis_ping = redis_client.ping()
        health_status = {
            "task_id": self.request.id,
            "status": "healthy",
            "timestamp": self.request.timestamp,
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available": memory.available,
            },
            "services": {
                "redis": redis_ping,
            },
        }
        logger.info("Health check completed", **health_status)
        return health_status
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "task_id": self.request.id,
            "status": "unhealthy",
            "error": str(e),
            "timestamp": self.request.timestamp,
        }


# Task utilities
def get_task_status(task_id: str) -> dict[str, Any]:
    """Get task status and result."""
    try:
        task_result = celery_app.AsyncResult(task_id)
        return {
            "task_id": task_id,
            "status": task_result.status,
            "result": (
                task_result.result if task_result.ready() else None
            ),
        }
    except Exception as e:
        logger.error(f"Failed to get task status for {task_id}: {e}")
        return {"task_id": task_id, "status": "UNKNOWN", "error": str(e)}


def cancel_task(task_id: str) -> bool:
    """Cancel a running task."""
    try:
        result = celery_app.AsyncResult(task_id)
        result.revoke(terminate=True)
        logger.info(f"Cancelled task {task_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to cancel task {task_id}: {e}")
        return False


def get_queue_stats() -> dict[str, Any]:
    """Get queue statistics."""
    try:
        inspect = celery_app.control.inspect()
        stats = {
            "active": inspect.active(),
            "reserved": inspect.reserved(),
            "scheduled": inspect.scheduled(),
            "registered": inspect.registered(),
            "stats": inspect.stats(),
        }
        return stats
    except Exception as e:
        logger.error(f"Failed to get queue stats: {e}")
        return {"error": str(e)}


# Worker management
def start_worker(queue: str = "default", concurrency: int = 4):
    """Start a Celery worker."""
    celery_app.worker_main(
        [
            "worker",
            "--loglevel=info",
            f"--queues={queue}",
            f"--concurrency={concurrency}",
            "--without-gossip",
            "--without-mingle",
            "--without-heartbeat",
        ]
    )


def start_beat():
    """Start Celery beat scheduler."""
    celery_app.worker_main(
        [
            "beat",
            "--loglevel=info",
            "--scheduler=celery.beat.PersistentScheduler",
        ]
    )


# Task decorators for common patterns
def with_retry(max_retries: int = 3, countdown: int = 60):
    """Decorator to add retry logic to tasks."""

    def decorator(func):
        func = celery_app.task(bind=True)(func)
        func.max_retries = max_retries
        func.default_retry_delay = countdown
        return func

    return decorator


def with_timeout(soft_time_limit: int = 300, time_limit: int = 600):
    """Decorator to add timeout to tasks."""

    def decorator(func):
        func = celery_app.task(bind=True)(func)
        func.soft_time_limit = soft_time_limit
        func.time_limit = time_limit
        return func

    return decorator


def with_rate_limit(rate_limit: str = "100/m"):
    """Decorator to add rate limiting to tasks."""

    def decorator(func):
        func = celery_app.task(bind=True)(func)
        func.rate_limit = rate_limit
        return func

    return decorator


if __name__ == "__main__":
    celery_app.start()
