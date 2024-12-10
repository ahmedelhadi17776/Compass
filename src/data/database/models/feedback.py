"""Feedback and comment models."""
from datetime import datetime
from enum import Enum
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, 
    Text, JSON, Index, Boolean, Enum as SQLAEnum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base
from .user import User

class FeedbackType(str, Enum):
    """Feedback type enum."""
    BUG = "bug"
    FEATURE = "feature"
    IMPROVEMENT = "improvement"
    QUESTION = "question"
    OTHER = "other"

class FeedbackStatus(str, Enum):
    """Feedback status enum."""
    NEW = "new"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    DUPLICATE = "duplicate"

class FeedbackPriority(str, Enum):
    """Feedback priority enum."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class Feedback(Base):
    """Feedback model."""
    __tablename__ = "feedback"
    __table_args__ = (
        Index('ix_feedback_user', 'user_id'),
        Index('ix_feedback_type', 'type'),
        Index('ix_feedback_status', 'status'),
        Index('ix_feedback_priority', 'priority'),
        {'extend_existing': True}
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("User.id", ondelete='SET NULL',name='fk_feedback_user_id'))
    type = Column(SQLAEnum(FeedbackType), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    status = Column(SQLAEnum(FeedbackStatus), nullable=False, default=FeedbackStatus.NEW)
    priority = Column(SQLAEnum(FeedbackPriority), nullable=False, default=FeedbackPriority.MEDIUM)
    
    # Additional Data
    category = Column(String(100))
    context = Column(JSON)  # Application context when feedback was given
    add_data = Column(JSON)  # Additional metadata
    tags = Column(JSON)
    
    # Resolution
    resolution = Column(Text)
    resolved_by = Column(Integer, ForeignKey("User.id"))
    resolved_at = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="feedback")
    resolver = relationship("User", foreign_keys=[resolved_by])
    comments = relationship("FeedbackComment", back_populates="feedback", cascade="all, delete-orphan")

class FeedbackComment(Base):
    """Feedback comment model."""
    __tablename__ = "feedback_comments"
    __table_args__ = (
        Index('ix_feedback_comments_feedback', 'feedback_id'),
        Index('ix_feedback_comments_user', 'user_id'),
        {'extend_existing': True}
    )

    id = Column(Integer, primary_key=True)
    feedback_id = Column(Integer, ForeignKey("feedback.id", ondelete='CASCADE',name='fk_feedback_comm_feedback'), nullable=False)
    user_id = Column(Integer, ForeignKey("User.id", ondelete='SET NULL',name='fk_feedback_comm_user_id'))
    content = Column(Text, nullable=False)
    is_internal = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    feedback = relationship("Feedback", back_populates="comments")
    user = relationship("User", back_populates="feedback_comments")
