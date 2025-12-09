# src/main.py
"""
FastAPI Application Entry Point
================================
Main application file with all routes and middleware

This creates:
- FastAPI app instance
- API routes (/health, /metrics, etc.)
- Middleware (CORS, logging, etc.)
- Metrics collection (Prometheus)
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from src.config import get_settings
from src.monitoring.metrics import setup_metrics, track_request
import time
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()

# ============================================
# CREATE FASTAPI APP
# ============================================

app = FastAPI(
    title=settings.APP_NAME,
    description="AI-Powered Meeting Intelligence Platform with Live Transcription",
    version="1.0.0",
    docs_url="/docs",      # Swagger UI at /docs
    redoc_url="/redoc",    # ReDoc at /redoc
    debug=settings.DEBUG
)

logger.info(f"Starting {settings.APP_NAME} in {settings.ENV} mode")

# ============================================
# MIDDLEWARE
# ============================================

# CORS - Allow frontend to call API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging and timing
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Log all requests and track response time
    
    For every request:
    - Log request details
    - Measure response time
    - Track metrics (Prometheus)
    """
    start_time = time.time()
    
    # Log request
    logger.info(f"→ {request.method} {request.url.path}")
    
    # Process request
    response = await call_next(request)
    
    # Calculate duration
    duration = time.time() - start_time
    
    # Log response
    logger.info(
        f"← {request.method} {request.url.path} "
        f"Status: {response.status_code} "
        f"Duration: {duration:.3f}s"
    )
    
    # Track metrics
    track_request(
        method=request.method,
        endpoint=request.url.path,
        status_code=response.status_code,
        duration=duration
    )
    
    # Add response time header
    response.headers["X-Response-Time"] = f"{duration:.3f}s"
    
    return response

# ============================================
# EXCEPTION HANDLERS
# ============================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all uncaught exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if settings.DEBUG else "An error occurred",
            "path": request.url.path,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

# ============================================
# STARTUP / SHUTDOWN EVENTS
# ============================================

@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    logger.info("=" * 50)
    logger.info(f"🚀 Starting {settings.APP_NAME}")
    logger.info(f"   Environment: {settings.ENV}")
    logger.info(f"   Debug mode: {settings.DEBUG}")
    logger.info(f"   Database: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'Not configured'}")
    logger.info("=" * 50)
    
    # Initialize metrics
    setup_metrics(app)
    logger.info("✅ Metrics initialized")
    
    # Test database connection
    try:
        from src.db.session import get_db
        from src.db.models import Meeting
        
        with get_db() as db:
            count = db.query(Meeting).count()
            logger.info(f"✅ Database connected ({count} meetings)")
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
    
    # Test storage connection
    try:
        from src.utils.storage import get_storage_client
        storage = get_storage_client()
        logger.info("✅ Storage connected")
    except Exception as e:
        logger.error(f"❌ Storage connection failed: {e}")
    
    logger.info("🎉 Application ready!")

@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    logger.info("Shutting down application...")
    # Cleanup code here
    logger.info("👋 Application stopped")

# ============================================
# HEALTH CHECK ENDPOINTS
# ============================================

@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - API info"""
    return {
        "name": settings.APP_NAME,
        "version": "1.0.0",
        "status": "running",
        "environment": settings.ENV,
        "docs": "/docs",
        "health": "/health",
        "metrics": "/metrics"
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint
    
    Returns system status and service health
    Used by:
    - Load balancers
    - Monitoring systems
    - Docker health checks
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {}
    }
    
    # Check database
    try:
        from src.db.session import get_db
        from src.db.models import Meeting
        
        with get_db() as db:
            db.query(Meeting).count()
        health_status["services"]["database"] = "healthy"
    except Exception as e:
        health_status["services"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check storage
    try:
        from src.utils.storage import get_storage_client
        storage = get_storage_client()
        storage.client.bucket_exists(settings.MINIO_BUCKET)
        health_status["services"]["storage"] = "healthy"
    except Exception as e:
        health_status["services"]["storage"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check Redis
    try:
        import redis
        r = redis.from_url(settings.REDIS_URL)
        r.ping()
        health_status["services"]["redis"] = "healthy"
    except Exception as e:
        health_status["services"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    return health_status

@app.get("/health/live", tags=["Health"])
async def liveness_probe():
    """
    Kubernetes liveness probe
    Simple check - is the app running?
    """
    return {"status": "alive"}

@app.get("/health/ready", tags=["Health"])
async def readiness_probe():
    """
    Kubernetes readiness probe
    Is the app ready to serve traffic?
    """
    # Check critical services
    try:
        from src.db.session import get_db
        with get_db() as db:
            db.execute("SELECT 1")
        return {"status": "ready"}
    except:
        return JSONResponse(
            status_code=503,
            content={"status": "not ready"}
        )

# ============================================
# INFO ENDPOINTS
# ============================================

@app.get("/info", tags=["Info"])
async def app_info():
    """Application information"""
    return {
        "app_name": settings.APP_NAME,
        "version": "1.0.0",
        "environment": settings.ENV,
        "python_version": "3.11+",
        "features": {
            "batch_transcription": True,
            "live_transcription": True,
            "ai_analysis": True,
            "action_items": True,
            "vector_search": True,
            "notifications": True
        },
        "limits": {
            "max_file_size_mb": 500,
            "max_duration_hours": 3,
            "supported_formats": [".wav", ".mp3", ".m4a", ".flac"]
        }
    }

# ============================================
# METRICS ENDPOINT (for Prometheus)
# ============================================
# This is added by setup_metrics() in monitoring/metrics.py

# ============================================
# INCLUDE ROUTERS (we'll add these in Day 2)
# ============================================

# from src.api.routes import upload, meetings, live
# app.include_router(upload.router)
# app.include_router(meetings.router)
# app.include_router(live.router)
# ============================================
# INCLUDE API ROUTERS
# ============================================
from src.api.routes import upload, meetings

app.include_router(upload.router)
app.include_router(meetings.router)

logger.info("✅ API routes registered")

# ============================================
# RUN APPLICATION
# ============================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload on code changes (development only)
        log_level="info"
    )