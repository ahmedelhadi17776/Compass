"""Summary model for AI-generated task content."""
from datetime import datetime
from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship

from ..base import Base

class SummarizedContent(Base):
    """Model for storing AI-generated summaries of tasks."""
    __tablename__ = "summarized_content"
    __table_args__ = (
        Index('idx_summarized_content_task_id', 'task_id'),
        {'extend_existing': True}
    )

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete='CASCADE'), unique=True)
    summary = Column(Text, nullable=False)
    key_points = Column(Text)  # Stored as JSON string
    generated_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    task = relationship("Task", back_populates="summary")
