# src/monitoring/metrics.py
"""
Prometheus Metrics
==================
Tracks application metrics for monitoring

Metrics collected:
- HTTP request count
- Response times
- Error rates
- Active requests
- Database queries
- Custom business metrics
"""

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import FastAPI, Response
import time
import logging

logger = logging.getLogger(__name__)

# ============================================
# DEFINE METRICS
# ============================================

# HTTP Request Metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'Number of HTTP requests in progress',
    ['method', 'endpoint']
)

# Application Metrics
meetings_total = Counter(
    'meetings_total',
    'Total number of meetings processed',
    ['status']
)

meeting_processing_duration_seconds = Histogram(
    'meeting_processing_duration_seconds',
    'Time taken to process a meeting'
)

transcription_duration_seconds = Histogram(
    'transcription_duration_seconds',
    'Time taken to transcribe audio'
)

action_items_extracted_total = Counter(
    'action_items_extracted_total',
    'Total number of action items extracted'
)

# LLM API Metrics
llm_api_calls_total = Counter(
    'llm_api_calls_total',
    'Total LLM API calls',
    ['model', 'provider']
)

llm_tokens_used_total = Counter(
    'llm_tokens_used_total',
    'Total tokens used',
    ['model', 'provider']
)

llm_api_errors_total = Counter(
    'llm_api_errors_total',
    'Total LLM API errors',
    ['model', 'provider', 'error_type']
)

# Storage Metrics
storage_uploads_total = Counter(
    'storage_uploads_total',
    'Total file uploads'
)

storage_downloads_total = Counter(
    'storage_downloads_total',
    'Total file downloads'
)

storage_bytes_uploaded = Counter(
    'storage_bytes_uploaded',
    'Total bytes uploaded'
)

storage_bytes_downloaded = Counter(
    'storage_bytes_downloaded',
    'Total bytes downloaded'
)

# ============================================
# HELPER FUNCTIONS
# ============================================

def track_request(method: str, endpoint: str, status_code: int, duration: float):
    """
    Track HTTP request metrics
    
    Args:
        method: HTTP method (GET, POST, etc.)
        endpoint: Request path
        status_code: Response status code
        duration: Request duration in seconds
    """
    http_requests_total.labels(
        method=method,
        endpoint=endpoint,
        status_code=status_code
    ).inc()
    
    http_request_duration_seconds.labels(
        method=method,
        endpoint=endpoint
    ).observe(duration)

def track_meeting(status: str):
    """
    Track meeting processing
    
    Args:
        status: Meeting status (completed, failed, etc.)
    """
    meetings_total.labels(status=status).inc()

def track_meeting_processing_time(duration: float):
    """
    Track how long meeting processing took
    
    Args:
        duration: Processing time in seconds
    """
    meeting_processing_duration_seconds.observe(duration)

def track_transcription_time(duration: float):
    """
    Track transcription duration
    
    Args:
        duration: Transcription time in seconds
    """
    transcription_duration_seconds.observe(duration)

def track_action_items(count: int):
    """
    Track number of action items extracted
    
    Args:
        count: Number of action items
    """
    action_items_extracted_total.inc(count)

def track_llm_call(model: str, provider: str, tokens: int):
    """
    Track LLM API usage
    
    Args:
        model: Model name (e.g., "llama-3.1-70b")
        provider: Provider name (e.g., "groq")
        tokens: Number of tokens used
    """
    llm_api_calls_total.labels(model=model, provider=provider).inc()
    llm_tokens_used_total.labels(model=model, provider=provider).inc(tokens)

def track_llm_error(model: str, provider: str, error_type: str):
    """
    Track LLM API errors
    
    Args:
        model: Model name
        provider: Provider name
        error_type: Type of error (timeout, rate_limit, etc.)
    """
    llm_api_errors_total.labels(
        model=model,
        provider=provider,
        error_type=error_type
    ).inc()

def track_storage_upload(size_bytes: int):
    """
    Track file upload
    
    Args:
        size_bytes: File size in bytes
    """
    storage_uploads_total.inc()
    storage_bytes_uploaded.inc(size_bytes)

def track_storage_download(size_bytes: int):
    """
    Track file download
    
    Args:
        size_bytes: File size in bytes
    """
    storage_downloads_total.inc()
    storage_bytes_downloaded.inc(size_bytes)

# ============================================
# CONTEXT MANAGERS
# ============================================

class track_time:
    """
    Context manager to track operation duration
    
    Usage:
        with track_time() as timer:
            # Do some work
            process_meeting()
        
        duration = timer.duration
        track_meeting_processing_time(duration)
    """
    def __init__(self):
        self.start_time = None
        self.duration = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.duration = time.time() - self.start_time
        return False

# ============================================
# SETUP FUNCTION
# ============================================

def setup_metrics(app: FastAPI):
    """
    Add metrics endpoint to FastAPI app
    
    This creates the /metrics endpoint that Prometheus scrapes
    
    Args:
        app: FastAPI application instance
    """
    
    @app.get("/metrics", tags=["Monitoring"], include_in_schema=False)
    async def metrics():
        """
        Prometheus metrics endpoint
        
        Returns metrics in Prometheus text format
        This endpoint is scraped by Prometheus every 15 seconds
        
        Example metrics output:
            # HELP http_requests_total Total HTTP requests
            # TYPE http_requests_total counter
            http_requests_total{method="GET",endpoint="/health",status_code="200"} 42.0
            
            # HELP http_request_duration_seconds HTTP request duration
            # TYPE http_request_duration_seconds histogram
            http_request_duration_seconds_bucket{method="GET",endpoint="/health",le="0.005"} 30.0
        """
        return Response(
            content=generate_latest(),
            media_type=CONTENT_TYPE_LATEST
        )
    
    logger.info("✅ Metrics endpoint registered at /metrics")

# ============================================
# EXAMPLE USAGE IN CODE
# ============================================

"""
Example: Track meeting processing

from src.monitoring.metrics import (
    track_meeting,
    track_meeting_processing_time,
    track_transcription_time,
    track_action_items,
    track_time
)

def process_meeting(meeting_id):
    with track_time() as timer:
        # Transcribe
        with track_time() as transcribe_timer:
            transcript = transcribe_audio(...)
        track_transcription_time(transcribe_timer.duration)
        
        # Extract action items
        action_items = extract_actions(transcript)
        track_action_items(len(action_items))
    
    # Track overall processing
    track_meeting_processing_time(timer.duration)
    track_meeting(status="completed")
"""