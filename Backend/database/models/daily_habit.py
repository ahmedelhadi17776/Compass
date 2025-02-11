"""Daily Habit model for tracking habits."""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base


class DailyHabit(Base):
    """Model for tracking daily habits."""
    __tablename__ = "daily_habits"
    __table_args__ = (
        Index('ix_daily_habits_user', 'user_id'),
        Index('ix_daily_habits_status', 'status'),
        {'extend_existing': True}
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey(
        "users.id", ondelete='CASCADE'), nullable=False)
    habit_name = Column(String(255), nullable=False)
    frequency = Column(String(50), default='daily')  # e.g., 'daily', 'weekly'
    status = Column(String(50), default='active')  # e.g., 'active', 'inactive'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="daily_habits")

    def __repr__(self):
        return f"<DailyHabit(id={self.id}, name='{self.habit_name}', status='{self.status}')>"
