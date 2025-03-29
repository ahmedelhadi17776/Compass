from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float, JSON, Text, Index, Enum
from sqlalchemy.orm import relationship
from Backend.data_layer.database.models.base import Base
from Backend.data_layer.database.models.calendar_event import CalendarEvent
from Backend.data_layer.database.models.task import TaskStatus, TaskPriority
import datetime
from sqlalchemy.sql import func


class EventOccurrence(Base):
    """Model for storing modifications to specific occurrences of recurring Events.

    This model allows tracking changes to individual occurrences of recurring Events
    without modifying the original recurring Event pattern.
    """
    __tablename__ = "event_occurrences"

    id = Column(Integer, primary_key=True, index=True)
    calendar_event_id = Column(Integer, ForeignKey(
        "calendar_events.id", ondelete="CASCADE"), nullable=False, index=True)
    # Which occurrence this is (0-based)
    occurrence_num = Column(Integer, nullable=False)
    # The specific date of this occurrence
    start_date = Column(DateTime, nullable=False)
    # Can be different from the original Event
    duration = Column(Float, nullable=True)
    # Can be different from the original Event
    due_date = Column(DateTime, nullable=True)

    # Fields that can be modified for a specific occurrence
    # If null, use original Event title
    title = Column(String(255), nullable=True)
    # If null, use original Event description
    description = Column(Text, nullable=True)
    # If null, use original task status
    status = Column(Enum(TaskStatus), nullable=True)
    # If null, use original task priority
    priority = Column(Enum(TaskPriority), nullable=True)

    # Additional fields for tracking
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow,
                        onupdate=datetime.datetime.utcnow)
    modified_by_id = Column(Integer, ForeignKey(
        "users.id"), nullable=False)  # Who modified this occurrence

    # Relationships
    calendar_event = relationship("CalendarEvent", back_populates="occurrences")
    modified_by = relationship("User", foreign_keys=[modified_by_id])


    __table_args__ = (
        # Ensure each occurrence of a task is unique
        Index("ix_event_occurrence_unique", "calendar_event_id",
              "occurrence_num", unique=True),
        Index("ix_event_occurrence_start_date", "start_date"),
        Index("ix_event_occurrence_due_date", "due_date"),
    )
