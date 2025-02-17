from sqlalchemy import Column, Integer, Text, ForeignKey, DateTime, Boolean, Float, JSON, Index
from sqlalchemy.orm import relationship
from Backend.data_layer.database.models.base import Base
import datetime

class TaskComment(Base):
    __tablename__ = "task_comments"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    parent_id = Column(Integer, ForeignKey("task_comments.id"))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # AI-specific fields
    is_ai_generated = Column(Boolean, default=False)
    ai_model_id = Column(Integer, ForeignKey("ai_models.id"))
    ai_confidence_score = Column(Float)  # Confidence in response accuracy
    ai_context_used = Column(JSON)  # Context chunks used for response
    ai_generated_keywords = Column(JSON)  # Key topics identified
    sentiment_analysis = Column(JSON)  # AI analysis of comment sentiment
    suggested_actions = Column(JSON)  # AI-suggested next steps
    reference_sources = Column(JSON)  # Sources used by AI

    # Relationships
    task = relationship("Task", back_populates="comments")
    user = relationship("User", foreign_keys=[user_id])
    parent = relationship("TaskComment", remote_side=[id], backref="replies")
    ai_model = relationship("AIModel", foreign_keys=[ai_model_id])

    __table_args__ = (
        Index("ix_task_comments_task_id", "task_id"),
        Index("ix_task_comments_user_id", "user_id"),
        Index("ix_task_comments_created_at", "created_at"),
        Index("ix_task_comments_is_ai_generated", "is_ai_generated"),
        Index("ix_task_comments_ai_confidence_score", "ai_confidence_score"),
    ) 