# src/api/routes/websocket.py
"""
WebSocket Routes for Live Transcription
========================================
Real-time audio streaming and transcription
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from src.db.session import get_db_session
from src.db.models import Meeting, MeetingStatus
from src.db.repositories.meeting_repo import MeetingRepository
from src.core.live_transcription import LiveTranscriptionService
from datetime import datetime
import logging
import json
import asyncio
import uuid

router = APIRouter(prefix="/api/v1/ws", tags=["WebSocket"])
logger = logging.getLogger(__name__)

# Active sessions
active_sessions = {}

@router.websocket("/transcribe")
async def websocket_transcribe(websocket: WebSocket):
    """
    WebSocket endpoint for live transcription
    
    Protocol:
    1. Client connects
    2. Client sends: {"type": "start", "meeting_title": "...", "language": "en"}
    3. Server responds: {"type": "session_started", "session_id": "..."}
    4. Client sends audio chunks: {"type": "audio", "data": base64_audio}
    5. Server sends transcripts: {"type": "transcript", "text": "...", "is_final": true}
    6. Client sends: {"type": "stop"}
    7. Server responds: {"type": "session_ended", "meeting_id": 123}
    
    Audio format:
    - Sample rate: 16000 Hz
    - Channels: Mono
    - Format: PCM 16-bit
    - Chunk size: 1 second (16000 samples)
    """
    await websocket.accept()
    
    session_id = str(uuid.uuid4())
    logger.info(f"🔌 WebSocket connected: {session_id}")
    
    transcription_service = None
    meeting_id = None
    
    try:
        # Send welcome message
        await websocket.send_json({
            "type": "connected",
            "session_id": session_id,
            "message": "WebSocket connected. Send 'start' to begin."
        })
        
        while True:
            # Receive message from client
            message = await websocket.receive_text()
            data = json.loads(message)
            
            message_type = data.get("type")
            
            # Handle start command
            if message_type == "start":
                logger.info(f"📝 Starting transcription session: {session_id}")
                
                # Get meeting info
                meeting_title = data.get("meeting_title", f"Live Meeting {datetime.now().strftime('%Y-%m-%d %H:%M')}")
                language = data.get("language", "en")
                participants = data.get("participants", [])
                
                # Create meeting record
                from src.db.session import get_db
                with get_db() as db:
                    meeting_data = {
                        "title": meeting_title,
                        "status": MeetingStatus.PROCESSING,
                        "participants": participants,
                        "meeting_date": datetime.utcnow()
                    }
                    meeting = MeetingRepository.create(db, meeting_data)
                    meeting_id = meeting.id
                
                # Initialize live transcription service
                transcription_service = LiveTranscriptionService(
                    session_id=session_id,
                    language=language,
                    meeting_id=meeting_id
                )
                
                active_sessions[session_id] = {
                    "service": transcription_service,
                    "meeting_id": meeting_id,
                    "start_time": datetime.utcnow()
                }
                
                # Send session started
                await websocket.send_json({
                    "type": "session_started",
                    "session_id": session_id,
                    "meeting_id": meeting_id,
                    "message": "Transcription started. Send audio data."
                })
            
            # Handle audio data
            elif message_type == "audio":
                if not transcription_service:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Session not started. Send 'start' first."
                    })
                    continue
                
                # Get audio data (base64 encoded)
                audio_data = data.get("data")
                
                if audio_data:
                    # Process audio chunk
                    result = await transcription_service.process_audio_chunk(audio_data)
                    
                    if result:
                        # Send transcript back to client
                        await websocket.send_json({
                            "type": "transcript",
                            "text": result["text"],
                            "is_final": result["is_final"],
                            "timestamp": result["timestamp"],
                            "confidence": result.get("confidence", 1.0)
                        })
            
            # Handle stop command
            elif message_type == "stop":
                logger.info(f"⏹️ Stopping transcription session: {session_id}")
                
                if transcription_service:
                    # Finalize transcription
                    final_transcript = await transcription_service.finalize()
                    
                    # Save to database
                    from src.db.session import get_db
                    with get_db() as db:
                        meeting = MeetingRepository.get_by_id(db, meeting_id)
                        if meeting:
                            meeting.transcript = final_transcript["full_transcript"]
                            meeting.duration_seconds = final_transcript["duration"]
                            meeting.status = MeetingStatus.COMPLETED
                    
                    # Cleanup
                    if session_id in active_sessions:
                        del active_sessions[session_id]
                    
                    # Send final response
                    await websocket.send_json({
                        "type": "session_ended",
                        "session_id": session_id,
                        "meeting_id": meeting_id,
                        "final_transcript": final_transcript["full_transcript"],
                        "duration": final_transcript["duration"],
                        "word_count": len(final_transcript["full_transcript"].split())
                    })
                    
                    logger.info(f"✅ Session completed: {session_id}")
                    break
            
            # Handle ping/heartbeat
            elif message_type == "ping":
                await websocket.send_json({"type": "pong"})
            
            else:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown message type: {message_type}"
                })
    
    except WebSocketDisconnect:
        logger.info(f"🔌 WebSocket disconnected: {session_id}")
    
    except Exception as e:
        logger.error(f"❌ WebSocket error: {e}", exc_info=True)
        
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
        except:
            pass
    
    finally:
        # Cleanup
        if session_id in active_sessions:
            del active_sessions[session_id]
        
        logger.info(f"🧹 Cleaned up session: {session_id}")

@router.get("/sessions")
async def get_active_sessions():
    """
    Get list of active transcription sessions
    
    Returns:
        List of active sessions with metadata
    """
    sessions = []
    
    for session_id, session_data in active_sessions.items():
        sessions.append({
            "session_id": session_id,
            "meeting_id": session_data["meeting_id"],
            "start_time": session_data["start_time"].isoformat(),
            "duration": (datetime.utcnow() - session_data["start_time"]).total_seconds()
        })
    
    return {
        "active_sessions": len(sessions),
        "sessions": sessions
    }