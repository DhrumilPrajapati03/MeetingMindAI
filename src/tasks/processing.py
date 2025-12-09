# src/tasks/processing.py
"""
Meeting Processing Tasks
========================
Background tasks for processing meeting audio
"""

from src.tasks.celery_app import celery_app
from src.db.session import get_db
from src.db.models import Meeting, MeetingStatus
from src.db.repositories.meeting_repo import MeetingRepository
from src.agents.transcriber import get_transcriber_agent
from src.utils.storage import get_storage_client
from src.monitoring.metrics import track_meeting, track_meeting_processing_time
import logging
import time
from pathlib import Path
import tempfile

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="process_meeting")
def process_meeting_task(self, meeting_id: int):
    """
    Process meeting audio file
    
    Steps:
    1. Download audio from storage
    2. Transcribe with Whisper
    3. Clean transcript with LLM
    4. Save results to database
    5. Update status
    
    Args:
        meeting_id: ID of meeting to process
    
    Returns:
        dict: Processing results
    """
    logger.info(f"=" * 60)
    logger.info(f"🎬 Starting background processing for meeting {meeting_id}")
    logger.info(f"   Task ID: {self.request.id}")
    logger.info(f"=" * 60)
    
    start_time = time.time()
    
    try:
        # Step 1: Get meeting from database
        with get_db() as db:
            meeting = MeetingRepository.get_by_id(db, meeting_id)
            
            if not meeting:
                logger.error(f"❌ Meeting {meeting_id} not found")
                return {"status": "error", "message": "Meeting not found"}
            
            if meeting.status == MeetingStatus.COMPLETED:
                logger.warning(f"⚠️  Meeting {meeting_id} already processed")
                return {"status": "already_processed"}
            
            # Update to processing
            meeting.status = MeetingStatus.PROCESSING
            logger.info(f"   Status: {meeting.status.value}")
        
        # Step 2: Download audio from storage
        logger.info(f"📥 Downloading audio from storage...")
        storage_client = get_storage_client()
        
        # Extract object name from path (e.g., "meeting-audio/meetings/file.wav" -> "meetings/file.wav")
        object_name = meeting.audio_file_path.split("/", 1)[1]
        audio_data = storage_client.download_file(object_name)
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            temp_file.write(audio_data)
            temp_audio_path = temp_file.name
        
        logger.info(f"   ✅ Downloaded: {len(audio_data)} bytes")
        
        # Step 3: Transcribe
        logger.info(f"🎙️ Starting transcription...")
        
        transcriber = get_transcriber_agent()
        result = transcriber.transcribe_audio(
            audio_path=temp_audio_path,
            meeting_context={
                "title": meeting.title,
                "description": meeting.description,
                "participants": meeting.participants
            }
        )
        
        logger.info(f"   ✅ Transcription complete: {result['word_count']} words")
        
        # Step 4: Save results to database
        logger.info(f"💾 Saving results to database...")
        
        with get_db() as db:
            meeting = MeetingRepository.get_by_id(db, meeting_id)
            
            # Update meeting with results
            meeting.transcript = result["cleaned_transcript"]
            meeting.duration_seconds = result["duration"]
            meeting.processing_time_seconds = result["processing_time"]
            meeting.status = MeetingStatus.COMPLETED
            
            # TODO: Extract action items (we'll add this in next phase)
            # TODO: Generate summary (we'll add this in next phase)
            
            logger.info(f"   ✅ Database updated")
        
        # Step 5: Cleanup
        Path(temp_audio_path).unlink(missing_ok=True)
        
        # Track metrics
        total_time = time.time() - start_time
        track_meeting_processing_time(total_time)
        track_meeting("completed")
        
        logger.info(f"=" * 60)
        logger.info(f"✅ Meeting {meeting_id} processed successfully!")
        logger.info(f"   Total time: {total_time:.1f}s")
        logger.info(f"=" * 60)
        
        return {
            "status": "success",
            "meeting_id": meeting_id,
            "word_count": result["word_count"],
            "duration": result["duration"],
            "processing_time": total_time
        }
    
    except Exception as e:
        logger.error(f"❌ Processing failed for meeting {meeting_id}: {e}", exc_info=True)
        
        # Update status to failed
        try:
            with get_db() as db:
                meeting = MeetingRepository.get_by_id(db, meeting_id)
                if meeting:
                    meeting.status = MeetingStatus.FAILED
            
            track_meeting("failed")
        except:
            pass
        
        # Retry task (max 3 retries, exponential backoff)
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries), max_retries=3)

@celery_app.task(name="get_meeting_status")
def get_meeting_status_task(meeting_id: int):
    """
    Get current status of meeting processing
    
    Args:
        meeting_id: Meeting ID
    
    Returns:
        dict: Status information
    """
    try:
        with get_db() as db:
            meeting = MeetingRepository.get_by_id(db, meeting_id)
            
            if not meeting:
                return {"status": "not_found"}
            
            return {
                "status": meeting.status.value,
                "progress": {
                    "uploading": 10,
                    "processing": 50,
                    "completed": 100,
                    "failed": 0
                }.get(meeting.status.value, 0),
                "has_transcript": bool(meeting.transcript),
                "word_count": len(meeting.transcript.split()) if meeting.transcript else 0
            }
    
    except Exception as e:
        logger.error(f"Failed to get status for meeting {meeting_id}: {e}")
        return {"status": "error", "message": str(e)}