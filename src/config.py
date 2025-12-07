# src/config.py
"""
Configuration Management
========================
Centralized configuration loaded from environment variables

This file uses Pydantic to:
- Load variables from .env file
- Validate types (string, int, bool, etc.)
- Provide defaults
- Give helpful errors if required variables are missing
"""

from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional
import os

class Settings(BaseSettings):
    """
    Application settings
    
    All these values come from .env file
    Example: GROQ_API_KEY in .env becomes settings.GROQ_API_KEY in code
    """
    
    # ============================================
    # APPLICATION
    # ============================================
    APP_NAME: str = "MeetingMind AI"
    ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str  # Required, no default
    
    # ============================================
    # DATABASE - PostgreSQL
    # ============================================
    DATABASE_URL: str
    # Example: postgresql://meetingmind:password@localhost:5432/meetingmind
    
    # ============================================
    # REDIS - Cache & Message Broker
    # ============================================
    REDIS_URL: str
    # Example: redis://localhost:6379/0
    
    # ============================================
    # QDRANT - Vector Database
    # ============================================
    QDRANT_URL: str
    QDRANT_API_KEY: Optional[str] = ""
    
    # ============================================
    # MINIO - Object Storage
    # ============================================
    MINIO_ENDPOINT: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_BUCKET: str = "meeting-audio"
    MINIO_SECURE: bool = False
    
    # ============================================
    # AI SERVICES
    # ============================================
    GROQ_API_KEY: str  # Required
    OPENAI_API_KEY: Optional[str] = ""
    
    # ============================================
    # MONITORING
    # ============================================
    SENTRY_DSN: Optional[str] = ""
    PROMETHEUS_PORT: int = 9090
    
    # ============================================
    # INTEGRATIONS
    # ============================================
    SLACK_BOT_TOKEN: Optional[str] = ""
    SLACK_CHANNEL_ID: Optional[str] = ""
    SMTP_HOST: Optional[str] = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = ""
    SMTP_PASSWORD: Optional[str] = ""
    
    # ============================================
    # CELERY - Task Queue
    # ============================================
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str
    
    class Config:
        """Pydantic configuration"""
        env_file = ".env"
        case_sensitive = True  # GROQ_API_KEY != groq_api_key

@lru_cache()  # Cache the settings (create only once, reuse)
def get_settings() -> Settings:
    """
    Get application settings (singleton pattern)
    
    Usage in other files:
        from src.config import get_settings
        settings = get_settings()
        print(settings.GROQ_API_KEY)
    """
    return Settings()

# Convenience: Import directly
settings = get_settings()