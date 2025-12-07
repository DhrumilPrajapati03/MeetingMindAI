# scripts/init_db.py
"""
Initialize Database
===================
Creates all tables in PostgreSQL
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.db.session import init_db
from src.db.models import Meeting, ActionItem
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Create all database tables"""
    logger.info("=" * 50)
    logger.info("Initializing Database")
    logger.info("=" * 50)
    
    try:
        init_db()
        logger.info("✅ Database initialized successfully!")
        logger.info("Tables created:")
        logger.info("  - meetings")
        logger.info("  - action_items")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()