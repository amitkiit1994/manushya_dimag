"""
Celery application configuration for Manushya.ai
"""

from celery import Celery

from manushya.config import settings

# Create Celery app
celery_app = Celery(
    "manushya",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["manushya.tasks.memory_tasks"],
)

# Celery configuration
celery_app.conf.update(
    task_serializer=settings.celery_task_serializer,
    result_serializer=settings.celery_result_serializer,
    accept_content=settings.celery_accept_content_list,
    task_always_eager=False,  # Set to True for testing
    task_eager_propagates=True,
    task_ignore_result=False,
    task_store_errors_even_if_ignored=True,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    worker_disable_rate_limits=False,
    task_compression="gzip",
    result_compression="gzip",
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=240,  # 4 minutes
    worker_send_task_events=True,
    task_send_sent_event=True,
    event_queue_expires=60,
    worker_state_db=None,
    worker_log_format="[%(asctime)s: %(levelname)s/%(processName)s] %(message)s",
    worker_task_log_format="[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s",
)

# Task routing
celery_app.conf.task_routes = {
    "manushya.tasks.memory_tasks.*": {"queue": "memory"},
    "manushya.tasks.cleanup_tasks.*": {"queue": "cleanup"},
}

# Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    "cleanup-expired-memories": {
        "task": "manushya.tasks.cleanup_tasks.cleanup_expired_memories",
        "schedule": 3600.0,  # Every hour
    },
    "cleanup-audit-logs": {
        "task": "manushya.tasks.cleanup_tasks.cleanup_old_audit_logs",
        "schedule": 86400.0,  # Every day
    },
}

if __name__ == "__main__":
    celery_app.start()
