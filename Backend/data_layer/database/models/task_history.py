from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON, Text, Boolean, Float, Index
from sqlalchemy.orm import relationship
from Backend.data_layer.database.models.base import Base
import datetime

class TaskHistory(Base):
    __tablename__ = "task_history"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(100), nullable=False)
    field = Column(String(100))
    old_value = Column(Text)
    new_value = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # AI-specific fields
    is_ai_generated = Column(Boolean, default=False)  # Whether the change was made by AI
    ai_model_id = Column(Integer, ForeignKey("ai_models.id"))  # Which AI model made the change
    ai_confidence_score = Column(Float)  # Confidence level of AI decision
    ai_reasoning = Column(Text)  # AI's explanation for the change
    ai_context_used = Column(JSON)  # Context data used by AI for decision

    # Relationships
    task = relationship("Task", back_populates="history")
    user = relationship("User", foreign_keys=[user_id])
    ai_model = relationship("AIModel", foreign_keys=[ai_model_id])

    __table_args__ = (
        Index("ix_task_history_task_id", "task_id"),
        Index("ix_task_history_user_id", "user_id"),
        Index("ix_task_history_created_at", "created_at"),
        Index("ix_task_history_is_ai_generated", "is_ai_generated"),
    ) 