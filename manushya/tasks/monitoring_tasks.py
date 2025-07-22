"""
Monitoring tasks for Manushya.ai
"""

import logging
import psutil
from typing import Any

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def update_system_metrics() -> dict[str, Any]:
    """Update system metrics."""
    try:
        # Get basic system metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        metrics = {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_available": memory.available,
            "memory_total": memory.total,
            "disk_percent": disk.percent,
            "disk_free": disk.free,
            "disk_total": disk.total,
        }
        
        logger.info(f"System metrics updated: {metrics}")
        return {"status": "success", "metrics": metrics}
    except Exception as e:
        logger.error(f"Failed to update system metrics: {e}")
        return {"status": "error", "message": str(e)} 