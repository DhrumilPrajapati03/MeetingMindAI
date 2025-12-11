# src/tasks/processing.py
"""
Meeting Processing Tasks
========================
Background tasks for processing meeting audio with ALL AI agents
"""

from src.tasks.celery_app import celery_app
from src.db.session import get_db
from src.db.models import Meeting, ActionItem, MeetingStatus, ActionItemPriority
from src.db.repositories.meeting_repo import MeetingRepository, ActionItemRepository
from src.agents.orchestrator import get_orchestrator
from src.utils.storage import get_storage_client
from src.monitoring.metrics import track_meeting, track_meeting_processing_time
import logging
import time
from pathlib import Path
import tempfile
from datetime import datetime

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="process_meeting")
def process_meeting_task(self, meeting_id: int):
    """
    Process meeting audio file with FULL AI PIPELINE
    
    Pipeline:
    1. Download audio from storage
    2. Transcribe with Whisper
    3. Clean transcript with LLM
    4. Analyze content (topics, sentiment, decisions)
    5. Extract action items
    6. Generate summary
    7. Save all results to database
    
    Args:
        meeting_id: ID of meeting to process
    
    Returns:
        dict: Processing results
    """
    logger.info(f"=" * 70)
    logger.info(f"🎬 FULL MEETING PROCESSING - Meeting {meeting_id}")
    logger.info(f"   Task ID: {self.request.id}")
    logger.info(f"=" * 70)
    
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
            
            # Get meeting context
            meeting_context = {
                "title": meeting.title,
                "description": meeting.description,
                "participants": meeting.participants,
                "meeting_date": meeting.meeting_date.isoformat() if meeting.meeting_date else None
            }
        
        # Step 2: Download audio from storage
        logger.info(f"\n📥 Downloading audio from storage...")
        storage_client = get_storage_client()
        
        # Extract object name from path
        object_name = meeting.audio_file_path.split("/", 1)[1]
        audio_data = storage_client.download_file(object_name)
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            temp_file.write(audio_data)
            temp_audio_path = temp_file.name
        
        logger.info(f"   ✅ Downloaded: {len(audio_data)} bytes")
        
        # Step 3: Run FULL AI PIPELINE (all agents!)
        logger.info(f"\n🤖 Running AI Agent Pipeline...")
        logger.info(f"   Agents: Transcriber → Analyzer → Action Hunter → Summarizer")
        
        orchestrator = get_orchestrator()
        results = orchestrator.process_meeting_full(
            audio_path=temp_audio_path,
            meeting_context=meeting_context
        )
        
        # Step 4: Save ALL results to database
        logger.info(f"\n💾 Saving results to database...")
        
        with get_db() as db:
            meeting = MeetingRepository.get_by_id(db, meeting_id)
            
            # 4.1: Save transcript
            meeting.transcript = results['transcription']['cleaned_transcript']
            meeting.duration_seconds = results['transcription']['duration']
            
            # 4.2: Save analysis results
            analysis = results['analysis']
            meeting.key_topics = analysis.get('key_topics', [])
            meeting.sentiment_score = analysis.get('sentiment', {}).get('overall_score', 0.0)
            
            # 4.3: Save summary
            meeting.summary = results['summary']
            
            # 4.4: Save processing metrics
            meeting.processing_time_seconds = results['metadata']['total_processing_time']
            meeting.status = MeetingStatus.COMPLETED
            
            logger.info(f"   ✅ Meeting data saved")
            
            # 4.5: Save action items
            action_items = results['action_items']
            logger.info(f"   💼 Saving {len(action_items)} action items...")
            
            for item in action_items:
                # Parse due date
                due_date = None
                if item.get('due_date'):
                    try:
                        due_date = datetime.strptime(item['due_date'], '%Y-%m-%d')
                    except:
                        pass
                
                # Map priority
                priority_map = {
                    'low': ActionItemPriority.LOW,
                    'medium': ActionItemPriority.MEDIUM,
                    'high': ActionItemPriority.HIGH,
                    'critical': ActionItemPriority.CRITICAL
                }
                priority = priority_map.get(item.get('priority', 'medium'), ActionItemPriority.MEDIUM)
                
                # Create action item
                action_item_data = {
                    'meeting_id': meeting_id,
                    'title': item['title'],
                    'description': item.get('description'),
                    'assigned_to': item.get('assigned_to'),
                    'due_date': due_date,
                    'priority': priority,
                    'confidence_score': item.get('confidence', 0.5),
                    'transcript_snippet': item.get('snippet')
                }
                
                ActionItemRepository.create(db, action_item_data)
            
            logger.info(f"   ✅ Action items saved")
        
        # Step 5: Cleanup
        Path(temp_audio_path).unlink(missing_ok=True)
        
        # Track metrics
        total_time = time.time() - start_time
        track_meeting_processing_time(total_time)
        track_meeting("completed")
        
        # Build result summary
        result_summary = {
            "status": "success",
            "meeting_id": meeting_id,
            "results": {
                "transcript_words": results['metadata']['word_count'],
                "duration_seconds": results['metadata']['duration'],
                "key_topics": len(analysis.get('key_topics', [])),
                "action_items": len(action_items),
                "sentiment_score": analysis.get('sentiment', {}).get('overall_score', 0.0)
            },
            "processing": {
                "total_time": total_time,
                "transcription_time": results['transcription']['transcription_time'],
                "analysis_time": total_time - results['transcription']['processing_time']
            }
        }
        
        logger.info(f"\n" + "=" * 70)
        logger.info(f"✅ MEETING {meeting_id} FULLY PROCESSED!")
        logger.info(f"=" * 70)
        logger.info(f"   📝 Transcript: {results['metadata']['word_count']} words")
        logger.info(f"   🔍 Topics: {len(analysis.get('key_topics', []))}")
        logger.info(f"   💼 Action Items: {len(action_items)}")
        logger.info(f"   😊 Sentiment: {analysis.get('sentiment', {}).get('overall_score', 0.0):.2f}")
        logger.info(f"   ⏱️  Total Time: {total_time:.1f}s")
        logger.info(f"=" * 70)
        
        return result_summary
    
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