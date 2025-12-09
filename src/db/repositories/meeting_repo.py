# src/db/repositories/meeting_repo.py
"""
Meeting Repository
==================
Database operations for meetings
"""

from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from src.db.models import Meeting, ActionItem, MeetingStatus
from typing import Optional, List, Dict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class MeetingRepository:
    """Repository for meeting database operations"""
    
    @staticmethod
    def create(db: Session, meeting_data: Dict) -> Meeting:
        """
        Create a new meeting
        
        Args:
            db: Database session
            meeting_data: Meeting data dictionary
        
        Returns:
            Created meeting
        """
        meeting = Meeting(**meeting_data)
        db.add(meeting)
        db.flush()  # Get ID without committing
        logger.info(f"Created meeting: {meeting.id}")
        return meeting
    
    @staticmethod
    def get_by_id(db: Session, meeting_id: int) -> Optional[Meeting]:
        """Get meeting by ID"""
        return db.query(Meeting).filter(Meeting.id == meeting_id).first()
    
    @staticmethod
    def get_all(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        status: Optional[MeetingStatus] = None
    ) -> List[Meeting]:
        """
        Get all meetings with pagination
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum records to return
            status: Filter by status
        
        Returns:
            List of meetings
        """
        query = db.query(Meeting)
        
        if status:
            query = query.filter(Meeting.status == status)
        
        return query.order_by(desc(Meeting.created_at)).offset(skip).limit(limit).all()
    
    @staticmethod
    def count(db: Session, status: Optional[MeetingStatus] = None) -> int:
        """Count total meetings"""
        query = db.query(func.count(Meeting.id))
        
        if status:
            query = query.filter(Meeting.status == status)
        
        return query.scalar()
    
    @staticmethod
    def update(db: Session, meeting_id: int, update_data: Dict) -> Optional[Meeting]:
        """
        Update meeting
        
        Args:
            db: Database session
            meeting_id: Meeting ID
            update_data: Data to update
        
        Returns:
            Updated meeting or None
        """
        meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
        
        if not meeting:
            return None
        
        for key, value in update_data.items():
            if value is not None and hasattr(meeting, key):
                setattr(meeting, key, value)
        
        meeting.updated_at = datetime.utcnow()
        db.flush()
        
        logger.info(f"Updated meeting: {meeting_id}")
        return meeting
    
    @staticmethod
    def delete(db: Session, meeting_id: int) -> bool:
        """Delete meeting"""
        meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
        
        if not meeting:
            return False
        
        db.delete(meeting)
        db.flush()
        
        logger.info(f"Deleted meeting: {meeting_id}")
        return True
    
    @staticmethod
    def search(db: Session, query: str, limit: int = 10) -> List[Meeting]:
        """
        Search meetings by title or description
        
        Args:
            db: Database session
            query: Search query
            limit: Maximum results
        
        Returns:
            List of matching meetings
        """
        search_pattern = f"%{query}%"
        
        return db.query(Meeting).filter(
            (Meeting.title.ilike(search_pattern)) |
            (Meeting.description.ilike(search_pattern))
        ).order_by(desc(Meeting.created_at)).limit(limit).all()

class ActionItemRepository:
    """Repository for action item database operations"""
    
    @staticmethod
    def create(db: Session, action_item_data: Dict) -> ActionItem:
        """Create action item"""
        action_item = ActionItem(**action_item_data)
        db.add(action_item)
        db.flush()
        logger.info(f"Created action item: {action_item.id}")
        return action_item
    
    @staticmethod
    def get_by_meeting_id(db: Session, meeting_id: int) -> List[ActionItem]:
        """Get all action items for a meeting"""
        return db.query(ActionItem).filter(
            ActionItem.meeting_id == meeting_id
        ).order_by(ActionItem.created_at).all()
    
    @staticmethod
    def update(db: Session, action_item_id: int, update_data: Dict) -> Optional[ActionItem]:
        """Update action item"""
        action_item = db.query(ActionItem).filter(ActionItem.id == action_item_id).first()
        
        if not action_item:
            return None
        
        for key, value in update_data.items():
            if value is not None and hasattr(action_item, key):
                setattr(action_item, key, value)
        
        db.flush()
        logger.info(f"Updated action item: {action_item_id}")
        return action_item