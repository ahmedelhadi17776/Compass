from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float, JSON, Text, Index, Enum
from sqlalchemy.orm import relationship
from Backend.data_layer.database.models.base import Base
from Backend.data_layer.database.models.task import TaskStatus, TaskPriority
import datetime
from sqlalchemy.sql import func


class TaskOccurrence(Base):
    """Model for storing modifications to specific occurrences of recurring tasks.

    This model allows tracking changes to individual occurrences of recurring tasks
    without modifying the original recurring task pattern.
    """
    __tablename__ = "task_occurrences"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey(
        "tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    # Which occurrence this is (0-based)
    occurrence_num = Column(Integer, nullable=False)
    # The specific date of this occurrence
    start_date = Column(DateTime, nullable=False)
    # Can be different from the original task
    duration = Column(Float, nullable=True)
    # Can be different from the original task
    due_date = Column(DateTime, nullable=True)

    # Fields that can be modified for a specific occurrence
    # If null, use original task title
    title = Column(String(255), nullable=True)
    # If null, use original task description
    description = Column(Text, nullable=True)
    # If null, use original task status
    status = Column(Enum(TaskStatus), nullable=True)
    # If null, use original task priority
    priority = Column(Enum(TaskPriority), nullable=True)
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    category_id = Column(Integer, ForeignKey(
        "task_categories.id"), nullable=True)

    # Additional fields for tracking
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow,
                        onupdate=datetime.datetime.utcnow)
    modified_by_id = Column(Integer, ForeignKey(
        "users.id"), nullable=False)  # Who modified this occurrence

    # Additional metadata
    progress_metrics = Column(
        JSON, server_default=func.json('{}'), nullable=True)
    blockers = Column(JSON, server_default=func.json('[]'), nullable=True)
    health_score = Column(Float, nullable=True)
    risk_factors = Column(JSON, nullable=True)

    # Relationships
    task = relationship("Task", back_populates="occurrences")
    assignee = relationship("User", foreign_keys=[assignee_id])
    reviewer = relationship("User", foreign_keys=[reviewer_id])
    modified_by = relationship("User", foreign_keys=[modified_by_id])
    category = relationship("TaskCategory")

    __table_args__ = (
        # Ensure each occurrence of a task is unique
        Index("ix_task_occurrence_unique", "task_id",
              "occurrence_num", unique=True),
        Index("ix_task_occurrence_start_date", "start_date"),
        Index("ix_task_occurrence_due_date", "due_date"),
    )
