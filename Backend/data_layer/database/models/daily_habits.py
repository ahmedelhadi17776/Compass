from sqlalchemy import Column, Integer, String, Text, Boolean, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, date, timedelta
from Backend.data_layer.database.models.base import Base
from Backend.utils.datetime_utils import get_utc_now


class DailyHabit(Base):
    """Model for tracking daily habits with streak functionality."""

    __tablename__ = "daily_habits"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    habit_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    start_day = Column(Date, nullable=False, default=date.today)
    end_day = Column(Date, nullable=True)
    current_streak = Column(Integer, default=0, nullable=False)
    longest_streak = Column(Integer, default=0, nullable=False)
    is_completed = Column(Boolean, default=False, nullable=False)
    last_completed_date = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True),
                        default=get_utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now,
                        onupdate=get_utc_now, nullable=False)

    # Relationships
    user = relationship("User", back_populates="daily_habits")

    def to_dict(self):
        """Convert model to dictionary for caching."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'habit_name': self.habit_name,
            'description': self.description,
            'start_day': self.start_day.isoformat() if self.start_day else None,
            'end_day': self.end_day.isoformat() if self.end_day else None,
            'current_streak': self.current_streak,
            'longest_streak': self.longest_streak,
            'is_completed': self.is_completed,
            'last_completed_date': self.last_completed_date.isoformat() if self.last_completed_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def from_dict(cls, data):
        """Create model instance from dictionary."""
        if not data:
            return None

        # Convert ISO format strings back to dates/datetimes
        if data.get('start_day'):
            data['start_day'] = date.fromisoformat(data['start_day'])
        if data.get('end_day'):
            data['end_day'] = date.fromisoformat(data['end_day'])
        if data.get('last_completed_date'):
            data['last_completed_date'] = date.fromisoformat(
                data['last_completed_date'])
        if data.get('created_at'):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if data.get('updated_at'):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])

        return cls(**data)

    def mark_completed(self, completion_date=None):
        """
        Mark the habit as completed for today and update streak.

        Args:
            completion_date: Optional date to mark as completed (defaults to today)

        Returns:
            bool: True if streak was updated, False if already completed today
        """
        today = completion_date or date.today()

        # If already completed today, do nothing
        if self.is_completed and self.last_completed_date == today:
            return False

        # Check if this is consecutive with last completion
        if self.last_completed_date:
            yesterday = today - timedelta(days=1)

            if self.last_completed_date < yesterday:
                # Streak broken - reset to 1
                self.current_streak = 1
            else:
                # Streak continues
                self.current_streak += 1
        else:
            # First completion
            self.current_streak = 1

        # Update longest streak if needed
        if self.current_streak > self.longest_streak:
            self.longest_streak = self.current_streak

        # Mark as completed
        self.is_completed = True
        self.last_completed_date = today
        self.updated_at = get_utc_now()

        return True

    def reset_daily_completion(self):
        """Reset the daily completion status without affecting streak."""
        self.is_completed = False
        self.updated_at = get_utc_now()

    def check_streak_reset(self):
        """
        Check if streak should be reset due to missed day.

        Returns:
            bool: True if streak was reset, False otherwise
        """
        today = date.today()

        # If no last completion or last completion was before yesterday, reset streak
        if not self.last_completed_date or (today - self.last_completed_date).days > 1:
            if self.current_streak > 0:  # Only reset if there was a streak
                self.current_streak = 0
                self.updated_at = get_utc_now()
                return True

        return False
