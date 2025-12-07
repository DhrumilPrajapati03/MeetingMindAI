# src/db/session.py
"""
Database Session Management
===========================
Handles PostgreSQL connections and transactions

A "session" is like a conversation with the database:
- Open connection
- Do operations (INSERT, SELECT, UPDATE, DELETE)
- Commit (save) or Rollback (undo)
- Close connection
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from src.config import get_settings
from contextlib import contextmanager
from typing import Generator
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

# ============================================
# CREATE ENGINE
# ============================================
# This is the "factory" that creates database connections

engine = create_engine(
    settings.DATABASE_URL,
    
    # Connection pool settings
    pool_pre_ping=True,      # Test connections before using (detect dead connections)
    pool_size=10,            # Keep 10 connections open
    max_overflow=20,         # Can create 20 more if needed (total 30 max)
    pool_recycle=3600,       # Recycle connections after 1 hour
    
    # Logging (set to True to see all SQL queries)
    echo=False,              # Set to True for debugging
)

logger.info("Database engine created")

# ============================================
# SESSION FACTORY
# ============================================
# Creates new database sessions

SessionLocal = sessionmaker(
    autocommit=False,        # Don't auto-commit (we control it)
    autoflush=False,         # Don't auto-flush (we control it)
    bind=engine
)

# ============================================
# CONTEXT MANAGER (Python's 'with' statement)
# ============================================

@contextmanager
def get_db() -> Generator[Session, None, None]:
    """
    Get a database session with automatic cleanup
    
    Usage:
        with get_db() as db:
            meeting = db.query(Meeting).first()
            meeting.title = "New Title"
            # Automatically commits when exiting 'with' block
    
    If error occurs:
        - Automatically rolls back changes
        - Raises the error
        - Closes connection
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()  # Save all changes
        logger.debug("Database transaction committed")
    except Exception as e:
        db.rollback()  # Undo all changes
        logger.error(f"Database transaction failed: {e}")
        raise
    finally:
        db.close()  # Always close connection
        logger.debug("Database session closed")

# ============================================
# FASTAPI DEPENDENCY
# ============================================

def get_db_session() -> Generator[Session, None, None]:
    """
    Database session for FastAPI dependency injection
    
    Usage in FastAPI:
        @app.get("/meetings")
        def get_meetings(db: Session = Depends(get_db_session)):
            meetings = db.query(Meeting).all()
            return meetings
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ============================================
# UTILITY FUNCTIONS
# ============================================

def init_db():
    """
    Initialize database (create all tables)
    
    This will create the tables defined in models.py
    """
    from src.db.models import Base
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")

def drop_db():
    """
    Drop all tables (DANGEROUS! Only use in development)
    """
    from src.db.models import Base
    logger.warning("Dropping all database tables...")
    Base.metadata.drop_all(bind=engine)
    logger.info("Database tables dropped")

def reset_db():
    """
    Reset database (drop and recreate all tables)
    """
    drop_db()
    init_db()
    logger.info("Database reset complete")