# src/tasks/celery_app.py
"""
Celery Application Configuration
=================================
Sets up Celery for background task processing
"""

from celery import Celery
from src.config import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

# ============================================
# CREATE CELERY APP
# ============================================

celery_app = Celery(
    "meetingmind",
    broker=settings.CELERY_BROKER_URL,      # Redis for task queue
    backend=settings.CELERY_RESULT_BACKEND  # Redis for results
)

# ============================================
# CONFIGURATION
# ============================================

celery_app.conf.update(
    # Task settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Task execution
    task_track_started=True,
    task_time_limit=3600,      # 1 hour max per task
    task_soft_time_limit=3300,  # Warn at 55 minutes
    
    # Worker settings
    worker_prefetch_multiplier=1,  # Process one task at a time
    worker_max_tasks_per_child=50,  # Restart worker after 50 tasks (prevent memory leaks)
    
    # Result backend settings
    result_expires=86400,  # Results expire after 24 hours
    
    # Retry settings
    task_acks_late=True,  # Acknowledge task after completion (not before)
    task_reject_on_worker_lost=True,
)

# ============================================
# TASK ROUTES (organize tasks)
# ============================================

celery_app.conf.task_routes = {
    'src.tasks.processing.*': {'queue': 'processing'},
    'src.tasks.notifications.*': {'queue': 'notifications'},
}

logger.info("✅ Celery app configured")