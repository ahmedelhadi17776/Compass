from sqlalchemy import Column, Integer, JSON, ForeignKey, DateTime, Float, Text, Index
from sqlalchemy.orm import relationship
from data_layer.database.models.base import Base
import datetime

class DailySummary(Base):
    __tablename__ = "daily_summaries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    date = Column(DateTime, nullable=False)
    completed_tasks = Column(JSON)  # List of completed tasks
    pending_tasks = Column(JSON)  # List of pending tasks
    productivity_score = Column(Float)  # Overall productivity score
    focus_time = Column(Integer)  # Total focus time in minutes
    meeting_time = Column(Integer)  # Total meeting time in minutes
    ai_interactions = Column(JSON)  # Summary of AI interactions
    wellness_summary = Column(JSON)  # Summary of wellness metrics
    next_day_suggestions = Column(Text)  # AI-generated suggestions
    highlights = Column(JSON)  # Key achievements and milestones
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="daily_summaries")

    __table_args__ = (
        Index("ix_daily_summaries_user_id", "user_id"),
        Index("ix_daily_summaries_date", "date"),
        Index("ix_daily_summaries_productivity_score", "productivity_score"),
    ) 