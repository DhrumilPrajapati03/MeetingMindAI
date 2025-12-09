# src/api/routes/meetings.py
"""
Meeting Management API Routes
==============================
CRUD operations for meetings
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from src.db.session import get_db_session
from src.db.models import MeetingStatus
from src.db.repositories.meeting_repo import MeetingRepository, ActionItemRepository
from src.schemas.meeting import (
    MeetingResponse,
    MeetingDetailResponse,
    MeetingListResponse,
    MeetingUpdateRequest,
    ActionItemResponse,
    ActionItemUpdateRequest
)
from typing import Optional
import logging

router = APIRouter(prefix="/api/v1/meetings", tags=["Meetings"])
logger = logging.getLogger(__name__)

@router.get("", response_model=MeetingListResponse)
async def list_meetings(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum records to return"),
    status: Optional[MeetingStatus] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db_session)
):
    """
    Get list of meetings with pagination
    
    Example:
        GET /api/v1/meetings?skip=0&limit=10&status=completed
    """
    meetings = MeetingRepository.get_all(db, skip=skip, limit=limit, status=status)
    total = MeetingRepository.count(db, status=status)
    
    # Calculate word count from transcript if available
    meeting_responses = []
    for meeting in meetings:
        meeting_dict = MeetingResponse.from_orm(meeting).dict()
        if meeting.transcript:
            meeting_dict['word_count'] = len(meeting.transcript.split())
        meeting_responses.append(MeetingResponse(**meeting_dict))
    
    return MeetingListResponse(
        meetings=meeting_responses,
        total=total,
        page=skip // limit + 1,
        page_size=limit
    )

@router.get("/{meeting_id}", response_model=MeetingDetailResponse)
async def get_meeting(
    meeting_id: int,
    db: Session = Depends(get_db_session)
):
    """
    Get detailed meeting information
    
    Includes:
    - Full transcript
    - Summary
    - Action items
    - All metadata
    """
    meeting = MeetingRepository.get_by_id(db, meeting_id)
    
    if not meeting:
        raise HTTPException(404, f"Meeting {meeting_id} not found")
    
    # Get action items
    action_items = ActionItemRepository.get_by_meeting_id(db, meeting_id)
    
    # Build response
    meeting_dict = MeetingDetailResponse.from_orm(meeting).dict()
    meeting_dict['action_items'] = [ActionItemResponse.from_orm(ai) for ai in action_items]
    
    if meeting.transcript:
        meeting_dict['word_count'] = len(meeting.transcript.split())
    
    return MeetingDetailResponse(**meeting_dict)

@router.put("/{meeting_id}", response_model=MeetingResponse)
async def update_meeting(
    meeting_id: int,
    update_data: MeetingUpdateRequest,
    db: Session = Depends(get_db_session)
):
    """
    Update meeting metadata
    
    Can update:
    - Title
    - Description
    - Participants
    """
    update_dict = update_data.dict(exclude_unset=True)
    
    meeting = MeetingRepository.update(db, meeting_id, update_dict)
    
    if not meeting:
        raise HTTPException(404, f"Meeting {meeting_id} not found")
    
    db.commit()
    
    return MeetingResponse.from_orm(meeting)

@router.delete("/{meeting_id}")
async def delete_meeting(
    meeting_id: int,
    db: Session = Depends(get_db_session)
):
    """Delete meeting and all related data"""
    success = MeetingRepository.delete(db, meeting_id)
    
    if not success:
        raise HTTPException(404, f"Meeting {meeting_id} not found")
    
    db.commit()
    
    return {"message": f"Meeting {meeting_id} deleted successfully"}

@router.get("/search", response_model=MeetingListResponse)
async def search_meetings(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db_session)
):
    """
    Search meetings by title or description
    
    Example:
        GET /api/v1/meetings/search?q=budget&limit=10
    """
    meetings = MeetingRepository.search(db, q, limit=limit)
    
    return MeetingListResponse(
        meetings=[MeetingResponse.from_orm(m) for m in meetings],
        total=len(meetings),
        page=1,
        page_size=limit
    )

@router.get("/{meeting_id}/transcript")
async def get_transcript(
    meeting_id: int,
    format: str = Query("text", regex="^(text|json)$", description="Response format"),
    db: Session = Depends(get_db_session)
):
    """
    Get meeting transcript
    
    Formats:
    - text: Plain text
    - json: Structured with timestamps
    """
    meeting = MeetingRepository.get_by_id(db, meeting_id)
    
    if not meeting:
        raise HTTPException(404, f"Meeting {meeting_id} not found")
    
    if not meeting.transcript:
        raise HTTPException(404, "Transcript not available yet")
    
    if format == "text":
        return {"transcript": meeting.transcript}
    else:
        # TODO: Return segments with timestamps
        return {
            "transcript": meeting.transcript,
            "segments": []  # We'll add this when we store segments
        }

@router.put("/{meeting_id}/action-items/{action_item_id}", response_model=ActionItemResponse)
async def update_action_item(
    meeting_id: int,
    action_item_id: int,
    update_data: ActionItemUpdateRequest,
    db: Session = Depends(get_db_session)
):
    """
    Update action item status
    
    Can update:
    - Status (pending/in_progress/completed/cancelled)
    - Assigned person
    - Due date
    - Priority
    """
    # Verify meeting exists
    meeting = MeetingRepository.get_by_id(db, meeting_id)
    if not meeting:
        raise HTTPException(404, f"Meeting {meeting_id} not found")
    
    # Update action item
    update_dict = update_data.dict(exclude_unset=True)
    action_item = ActionItemRepository.update(db, action_item_id, update_dict)
    
    if not action_item:
        raise HTTPException(404, f"Action item {action_item_id} not found")
    
    if action_item.meeting_id != meeting_id:
        raise HTTPException(400, "Action item does not belong to this meeting")
    
    db.commit()
    
    return ActionItemResponse.from_orm(action_item)

@router.get("/{meeting_id}/status")
async def get_meeting_status(
    meeting_id: int,
    db: Session = Depends(get_db_session)
):
    """
    Get meeting processing status
    
    Returns:
    - Current status (uploading/processing/completed/failed)
    - Progress percentage
    - Available data (transcript, summary, etc.)
    """
    meeting = MeetingRepository.get_by_id(db, meeting_id)
    
    if not meeting:
        raise HTTPException(404, f"Meeting {meeting_id} not found")
    
    # Calculate progress
    progress_map = {
        MeetingStatus.UPLOADING: 10,
        MeetingStatus.PROCESSING: 50,
        MeetingStatus.COMPLETED: 100,
        MeetingStatus.FAILED: 0
    }
    
    return {
        "meeting_id": meeting_id,
        "status": meeting.status.value,
        "progress": progress_map.get(meeting.status, 0),
        "data_available": {
            "transcript": bool(meeting.transcript),
            "summary": bool(meeting.summary),
            "action_items": len(meeting.action_items) if meeting.action_items else 0
        },
        "processing_time": meeting.processing_time_seconds,
        "created_at": meeting.created_at,
        "updated_at": meeting.updated_at
    }