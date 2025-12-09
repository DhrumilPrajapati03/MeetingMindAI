# scripts/start_celery.py
"""
Start Celery Worker
===================
Starts the Celery worker to process background tasks
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.tasks.celery_app import celery_app
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Starting Celery Worker")
    logger.info("=" * 60)
    
    # Start worker
    celery_app.worker_main([
        'worker',
        '--loglevel=info',
        '--concurrency=2',  # Number of worker processes
        '--queues=processing,notifications',
        '--pool=solo' if sys.platform == 'win32' else '--pool=prefork'  # Windows uses solo
    ])