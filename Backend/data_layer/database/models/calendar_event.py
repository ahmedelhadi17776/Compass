from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime, Index
from sqlalchemy.orm import relationship
from data_layer.database.models.base import Base
import datetime


class CalendarEvent(Base):
    __tablename__ = "calendar_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    location = Column(String(255))
    is_all_day = Column(Boolean, default=False)
    external_id = Column(String(255))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow,
                        onupdate=datetime.datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="calendar_events")
    meeting_notes = relationship("MeetingNotes", back_populates="calendar_event", cascade="all, delete-orphan")
    linked_todos = relationship("Todo", back_populates="linked_calendar_event")

    __table_args__ = (
        Index("ix_calendar_events_user_id", "user_id"),
        Index("ix_calendar_events_start_time", "start_time"),
        Index("ix_calendar_events_end_time", "end_time"),
        Index("ix_calendar_events_external_id", "external_id"),
    )
