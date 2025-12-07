# src/db/models.py
"""
Database Models (Tables)
========================
Defines the structure of our PostgreSQL database using SQLAlchemy ORM

Instead of writing SQL:
    CREATE TABLE meetings (
        id SERIAL PRIMARY KEY,
        title VARCHAR(255),
        ...
    );

We write Python classes and SQLAlchemy generates the SQL!
"""

from sqlalchemy import Column, Integer, String, DateTime, Float, JSON, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

# Base class for all models
Base = declarative_base()

# ============================================
# ENUMS - Predefined choices
# ============================================

class MeetingStatus(str, enum.Enum):
    """
    Meeting processing status
    
    Workflow:
    UPLOADING → PROCESSING → COMPLETED
                    ↓
                  FAILED
    """
    UPLOADING = "uploading"      # File is being uploaded
    PROCESSING = "processing"     # AI is analyzing
    COMPLETED = "completed"       # Done!
    FAILED = "failed"            # Error occurred

class ActionItemStatus(str, enum.Enum):
    """Action item completion status"""
    PENDING = "pending"           # Not started
    IN_PROGRESS = "in_progress"   # Being worked on
    COMPLETED = "completed"       # Done
    CANCELLED = "cancelled"       # No longer needed

class ActionItemPriority(str, enum.Enum):
    """Action item priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

# ============================================
# MEETING TABLE
# ============================================

class Meeting(Base):
    """
    Main meeting table
    
    Stores everything about a meeting:
    - Basic info (title, date, participants)
    - Audio file location
    - AI-generated content (transcript, summary, insights)
    - Processing metrics (time, cost)
    
    Relationships:
    - One meeting has many action items
    """
    __tablename__ = "meetings"
    
    # ============================================
    # PRIMARY KEY
    # ============================================
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # ============================================
    # BASIC INFORMATION
    # ============================================
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # ============================================
    # FILE INFORMATION
    # ============================================
    audio_file_path = Column(String(512), nullable=True)
    # Example: "meeting-audio/meetings/abc-123.wav"
    
    duration_seconds = Column(Float, nullable=True)
    # Example: 3600.5 (1 hour meeting)
    
    # ============================================
    # PROCESSING STATUS
    # ============================================
    status = Column(
        SQLEnum(MeetingStatus),
        default=MeetingStatus.UPLOADING,
        nullable=False,
        index=True
    )
    
    # ============================================
    # AI-GENERATED CONTENT
    # ============================================
    transcript = Column(Text, nullable=True)
    # Full meeting transcript
    
    summary = Column(Text, nullable=True)
    # AI-generated summary
    
    key_topics = Column(JSON, nullable=True)
    # Example: ["budget planning", "Q4 goals", "hiring"]
    
    sentiment_score = Column(Float, nullable=True)
    # Range: -1.0 (very negative) to 1.0 (very positive)
    # Example: 0.7 (positive meeting)
    
    # ============================================
    # METADATA
    # ============================================
    participants = Column(JSON, nullable=True)
    # Example: ["Alice", "Bob", "Charlie"]
    
    meeting_date = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    # When the meeting happened
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    # When record was created
    
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    # When record was last updated
    
    # ============================================
    # PERFORMANCE TRACKING
    # ============================================
    processing_time_seconds = Column(Float, nullable=True)
    # How long did AI processing take?
    
    token_count = Column(Integer, nullable=True)
    # How many LLM tokens were used?
    
    cost_usd = Column(Float, nullable=True)
    # How much did this cost?
    
    # ============================================
    # RELATIONSHIPS
    # ============================================
    action_items = relationship(
        "ActionItem",
        back_populates="meeting",
        cascade="all, delete-orphan"  # Delete action items when meeting is deleted
    )
    
    def __repr__(self):
        return f"<Meeting(id={self.id}, title='{self.title}', status={self.status})>"

# ============================================
# ACTION ITEM TABLE
# ============================================

class ActionItem(Base):
    """
    Action items extracted from meetings
    
    Example: "Alice to send budget proposal to Bob by Friday"
    
    Extracted information:
    - title: "Send budget proposal"
    - assigned_to: "Alice"
    - due_date: 2024-12-13
    - priority: "high"
    """
    __tablename__ = "action_items"
    
    # ============================================
    # PRIMARY KEY
    # ============================================
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # ============================================
    # FOREIGN KEY (connects to Meeting)
    # ============================================
    meeting_id = Column(
        Integer,
        ForeignKey("meetings.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # ============================================
    # ACTION DETAILS
    # ============================================
    title = Column(String(500), nullable=False)
    # Example: "Send budget proposal to finance team"
    
    description = Column(Text, nullable=True)
    # More detailed explanation
    
    assigned_to = Column(String(255), nullable=True, index=True)
    # Who is responsible? Example: "Alice"
    
    due_date = Column(DateTime, nullable=True, index=True)
    # When is it due?
    
    priority = Column(
        SQLEnum(ActionItemPriority),
        default=ActionItemPriority.MEDIUM,
        nullable=False
    )
    
    status = Column(
        SQLEnum(ActionItemStatus),
        default=ActionItemStatus.PENDING,
        nullable=False,
        index=True
    )
    
    # ============================================
    # CONTEXT (where was this mentioned?)
    # ============================================
    transcript_snippet = Column(Text, nullable=True)
    # Exact quote from meeting
    # Example: "Alice, can you send the budget proposal by Friday?"
    
    confidence_score = Column(Float, nullable=True)
    # How confident is AI about this action item?
    # Range: 0.0 to 1.0
    # Example: 0.95 (very confident)
    
    # ============================================
    # TIMESTAMPS
    # ============================================
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    
    # ============================================
    # RELATIONSHIPS
    # ============================================
    meeting = relationship("Meeting", back_populates="action_items")
    
    def __repr__(self):
        return f"<ActionItem(id={self.id}, title='{self.title[:30]}...', status={self.status})>"

# ============================================
# FUTURE TABLES (we'll add these later)
# ============================================

# class User(Base):
#     """User accounts"""
#     __tablename__ = "users"
#     # Add in Day 2-3

# class MeetingParticipant(Base):
#     """Link meetings to participants"""
#     __tablename__ = "meeting_participants"
#     # Add in Day 2-3