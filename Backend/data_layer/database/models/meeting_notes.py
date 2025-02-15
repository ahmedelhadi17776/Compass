from sqlalchemy import Column, Integer, Text, JSON, ForeignKey, DateTime, Index
from sqlalchemy.orm import relationship
from data_layer.database.models.base import Base
import datetime


class MeetingNotes(Base):
    __tablename__ = "meeting_notes"

    id = Column(Integer, primary_key=True, index=True)
    calendar_event_id = Column(Integer, ForeignKey(
        "calendar_events.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey(
        "users.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text)
    ai_summary = Column(Text)  # AI-generated meeting summary
    action_items = Column(JSON)  # List of action items extracted
    attendees = Column(JSON)  # List of attendees and their roles
    transcription = Column(Text)  # Meeting transcription if available
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow,
                        onupdate=datetime.datetime.utcnow)

    # Relationships
    calendar_event = relationship(
        "CalendarEvent", back_populates="meeting_notes")
    user = relationship("User", back_populates="meeting_notes")

    __table_args__ = (
        Index("ix_meeting_notes_calendar_event_id", "calendar_event_id"),
        Index("ix_meeting_notes_user_id", "user_id"),
        Index("ix_meeting_notes_created_at", "created_at"),
    )
