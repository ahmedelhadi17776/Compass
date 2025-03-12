from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime, Index, Enum, Interval
from sqlalchemy.orm import relationship
from Backend.data_layer.database.models.base import Base
import datetime
import enum


class RecurrenceType(enum.Enum):
    NONE = "None"
    DAILY = "Daily"
    WEEKLY = "Weekly"
    MONTHLY = "Monthly"
    YEARLY = "Yearly"


class CalendarEvent(Base):
    __tablename__ = "calendar_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey(
        "users.id", ondelete="CASCADE"), nullable=False)
    task_id = Column(Integer, ForeignKey(
        "tasks.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    start_time = Column(DateTime, nullable=False)
    duration = Column(Interval, nullable=False, default=datetime.timedelta(
        hours=1))
    location = Column(String(255))
    is_all_day = Column(Boolean, default=False)
    external_id = Column(String(255))

    # Recurrence Fields
    recurrence = Column(Enum(RecurrenceType),
                        default=RecurrenceType.NONE, nullable=False)
    recurrence_end_date = Column(
        DateTime, nullable=True)  # When recurrence stops

    # Reminder Fields
    reminder_minutes_before = Column(Integer, nullable=True)
    # "email", "push", etc.
    notification_method = Column(String(50), nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow,
                        onupdate=datetime.datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="calendar_events")
    meeting_notes = relationship(
        "MeetingNotes", back_populates="calendar_event", cascade="all, delete-orphan")
    task = relationship("Task", back_populates="calendar_event", uselist=False)
    linked_todos = relationship("Todo", back_populates="linked_calendar_event")

    __table_args__ = (
        Index("ix_calendar_events_user_id", "user_id"),
        Index("ix_calendar_events_start_time", "start_time"),
        Index("ix_calendar_events_recurrence", "recurrence"),
        Index("ix_calendar_events_external_id", "external_id"),
    )
