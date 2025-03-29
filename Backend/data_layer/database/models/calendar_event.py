from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime, Index, Enum, Interval, Float
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import relationship
from Backend.data_layer.database.models.base import Base
import datetime
import enum
from Backend.data_layer.database.models.task import TaskStatus, TaskPriority


class RecurrenceType(enum.Enum):
    NONE = "None"
    DAILY = "Daily"
    WEEKLY = "Weekly"
    BIWEEKLY = "Biweekly"
    MONTHLY = "Monthly"
    YEARLY = "Yearly"
    CUSTOM = "Custom"

class EventType(enum.Enum):
    NONE = "None"
    TASK = "Task"
    MEETING = "Meeting"
    TODO = "Todo"
    HOLIDAY = "Holiday"
    REMINDER = "Reminder"

class CalendarEvent(Base):
    __tablename__ = "calendar_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey(
        "users.id", ondelete="CASCADE"), nullable=False)
    task_id = Column(Integer, ForeignKey(
        "tasks.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(Enum(TaskStatus),
                    default=TaskStatus.UPCOMING, nullable=False)
    priority = Column(Enum(TaskPriority),
                      default=TaskPriority.MEDIUM)
    event_type = Column(Enum(EventType),
                        default=EventType.NONE, nullable=False)
    start_date = Column(
        DateTime, default=datetime.datetime.utcnow, nullable=False)
    duration = Column(Float, nullable=True)
    due_date = Column(DateTime, nullable=True)
    location = Column(String(255))
    is_all_day = Column(Boolean, default=False)
    external_id = Column(String(255))

    # Recurrence Fields
    recurrence = Column(Enum(RecurrenceType),
                        default=RecurrenceType.NONE, nullable=False)
    recurrence_custom_days = Column(postgresql.ARRAY(String), nullable=True)
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
    occurrences = relationship(
        "EventOccurrence", back_populates="calendar_event", cascade="all, delete-orphan")
    task = relationship("Task", back_populates="calendar_event", uselist=False)
    linked_todos = relationship("Todo", back_populates="linked_calendar_event")

    __table_args__ = (
        Index("ix_calendar_events_user_id", "user_id"),
        Index("ix_calendar_events_start_date", "start_date"),
        Index("ix_calendar_events_due_date", "due_date"),
        Index("ix_calendar_events_recurrence", "recurrence"),
        Index("ix_calendar_events_external_id", "external_id"),
        Index("ix_calendar_events_status", "status"),
        Index("ix_calendar_events_priority", "priority"),
    )

