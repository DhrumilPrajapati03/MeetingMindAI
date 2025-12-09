# src/schemas/meeting.py
"""
Meeting Pydantic Schemas
========================
Request/response models for meeting endpoints
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

# ============================================
# ENUMS
# ============================================

class MeetingStatusEnum(str, Enum):
    """Meeting processing status"""
    UPLOADING = "uploading"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class ActionItemStatusEnum(str, Enum):
    """Action item status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class ActionItemPriorityEnum(str, Enum):
    """Action item priority"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

# ============================================
# REQUEST SCHEMAS
# ============================================

class MeetingUploadRequest(BaseModel):
    """Request for uploading a meeting"""
    title: str = Field(..., min_length=1, max_length=255, description="Meeting title")
    description: Optional[str] = Field(None, max_length=2000, description="Meeting description")
    participants: Optional[List[str]] = Field(None, description="List of participant names")
    meeting_date: Optional[datetime] = Field(None, description="When the meeting occurred")

class MeetingUpdateRequest(BaseModel):
    """Request for updating meeting metadata"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    participants: Optional[List[str]] = None

class ActionItemUpdateRequest(BaseModel):
    """Request for updating action item"""
    status: Optional[ActionItemStatusEnum] = None
    assigned_to: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: Optional[ActionItemPriorityEnum] = None

# ============================================
# RESPONSE SCHEMAS
# ============================================

class ActionItemResponse(BaseModel):
    """Action item response"""
    id: int
    title: str
    description: Optional[str]
    assigned_to: Optional[str]
    due_date: Optional[datetime]
    priority: str
    status: str
    confidence_score: Optional[float]
    transcript_snippet: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True

class MeetingResponse(BaseModel):
    """Meeting response"""
    id: int
    title: str
    description: Optional[str]
    status: str
    duration_seconds: Optional[float]
    word_count: Optional[int] = None
    participants: Optional[List[str]]
    meeting_date: datetime
    created_at: datetime
    updated_at: datetime
    
    # Processing info
    processing_time_seconds: Optional[float]
    cost_usd: Optional[float]
    
    class Config:
        from_attributes = True

class MeetingDetailResponse(MeetingResponse):
    """Detailed meeting response with transcript"""
    transcript: Optional[str]
    summary: Optional[str]
    key_topics: Optional[List[str]]
    sentiment_score: Optional[float]
    action_items: List[ActionItemResponse] = []

class MeetingUploadResponse(BaseModel):
    """Response after uploading meeting"""
    meeting_id: int
    message: str
    status: str
    estimated_processing_time: Optional[float]

class MeetingListResponse(BaseModel):
    """List of meetings"""
    meetings: List[MeetingResponse]
    total: int
    page: int
    page_size: int