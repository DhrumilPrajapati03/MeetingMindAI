# src/api/routes/upload.py
"""
Upload API Routes
=================
Handles meeting audio file uploads
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.orm import Session
from src.db.session import get_db_session
from src.db.models import Meeting, MeetingStatus
from src.db.repositories.meeting_repo import MeetingRepository
from src.schemas.meeting import MeetingUploadResponse
from src.utils.storage import get_storage_client
from src.core.audio_processor import AudioProcessor
from src.monitoring.metrics import track_storage_upload
from datetime import datetime
from typing import Optional, List
import uuid
import logging
from pathlib import Path
import io

router = APIRouter(prefix="/api/v1/upload", tags=["Upload"])
logger = logging.getLogger(__name__)

@router.post("", response_model=MeetingUploadResponse)
async def upload_meeting(
    file: UploadFile = File(..., description="Audio file (WAV, MP3, M4A, etc.)"),
    title: str = Form(..., description="Meeting title"),
    description: Optional[str] = Form(None, description="Meeting description"),
    participants: Optional[str] = Form(None, description="Comma-separated participant names"),
    db: Session = Depends(get_db_session)
):
    """
    Upload meeting audio file
    
    Steps:
    1. Validate audio file
    2. Upload to MinIO storage
    3. Create database record
    4. Trigger background processing (Celery)
    5. Return meeting ID
    
    Example:
        curl -X POST "http://localhost:8000/api/v1/upload" \
             -F "file=@meeting.wav" \
             -F "title=Q4 Planning Meeting" \
             -F "description=Quarterly planning discussion" \
             -F "participants=Alice,Bob,Charlie"
    """
    logger.info(f"📤 Upload request: {file.filename}")
    
    try:
        # Step 1: Validate file
        if not file.content_type or not file.content_type.startswith("audio/"):
            raise HTTPException(400, "Only audio files are supported")
        
        # Read file
        content = await file.read()
        file_size_mb = len(content) / (1024 * 1024)
        
        logger.info(f"   File size: {file_size_mb:.2f}MB")
        
        # Check size limit
        if file_size_mb > AudioProcessor.MAX_FILE_SIZE_MB:
            raise HTTPException(
                400,
                f"File too large: {file_size_mb:.1f}MB (max: {AudioProcessor.MAX_FILE_SIZE_MB}MB)"
            )
        
        # Step 2: Generate unique filename and upload to storage
        file_extension = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        object_name = f"meetings/{unique_filename}"
        
        logger.info(f"   Uploading to storage: {object_name}")
        
        storage_client = get_storage_client()
        file_io = io.BytesIO(content)
        
        storage_path = storage_client.upload_file(
            file_io,
            object_name,
            content_type=file.content_type
        )
        
        # Track metrics
        track_storage_upload(len(content))
        
        logger.info(f"   ✅ Uploaded: {storage_path}")
        
        # Step 3: Parse participants
        participant_list = None
        if participants:
            participant_list = [p.strip() for p in participants.split(",") if p.strip()]
        
        # Step 4: Create database record
        meeting_data = {
            "title": title,
            "description": description,
            "audio_file_path": storage_path,
            "participants": participant_list,
            "status": MeetingStatus.UPLOADING,
            "meeting_date": datetime.utcnow()
        }
        
        meeting = MeetingRepository.create(db, meeting_data)
        db.commit()
        
        logger.info(f"   ✅ Created meeting record: {meeting.id}")
        
        # Step 5: Estimate processing time
        # For now, rough estimate based on file size
        estimated_duration = file_size_mb * 10  # Rough: 10 seconds per MB
        estimated_processing = estimated_duration * 0.2  # 20% of duration
        
        # Step 6: Trigger background processing
        # We'll add Celery task in next step
        # For now, just update status
        meeting.status = MeetingStatus.PROCESSING
        db.commit()
        
        # TODO: Trigger Celery task
        from src.tasks.processing import process_meeting_task
        
        task = process_meeting_task.delay(meeting.id)
        
        logger.info(f"   ✅ Queued for processing: {meeting.id} (Task: {task.id})")
        
        return MeetingUploadResponse(
            meeting_id=meeting.id,
            message=f"Meeting uploaded successfully. Processing started.",
            status="processing",
            estimated_processing_time=estimated_processing
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"   ❌ Upload failed: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to upload meeting: {str(e)}")

@router.get("/formats")
async def get_supported_formats():
    """Get supported audio formats"""
    return {
        "supported_formats": AudioProcessor.SUPPORTED_FORMATS,
        "max_file_size_mb": AudioProcessor.MAX_FILE_SIZE_MB,
        "max_duration_hours": AudioProcessor.MAX_DURATION_HOURS
    }