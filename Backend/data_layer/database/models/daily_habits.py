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
    streak_start_date = Column(Date, nullable=True)
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
            'streak_start_date': self.streak_start_date.isoformat() if self.streak_start_date else None,
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
        if data.get('streak_start_date'):
            data['streak_start_date'] = date.fromisoformat(
                data['streak_start_date'])
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
                # Streak broken - reset to 0
                self.current_streak = 0
                # Set new streak start date when starting a new streak
                self.streak_start_date = today
            else:
                # Streak continues
                self.current_streak += 1
                # If this is the first completion in a streak, set the start date
                if self.current_streak == 1:
                    self.streak_start_date = self.last_completed_date
        else:
            # First completion
            self.current_streak = 1
            # Set streak start date for first completion
            self.streak_start_date = today

        # Update longest streak if needed
        if self.current_streak > self.longest_streak:
            self.longest_streak = self.current_streak

        # Mark as completed
        self.is_completed = True
        self.last_completed_date = today
        self.updated_at = get_utc_now()

        return True

    def unmark_completed(self):
        """
        Unmark a habit that was accidentally marked as completed.
        This will revert the streak changes made by the mark_completed method.
        
        Returns:
            bool: True if unmarking was successful, False if not applicable
        """
        today = date.today()
        
        # Can only unmark if it was completed today
        if not self.is_completed or self.last_completed_date != today:
            return False
        
        # Store original values to determine if longest_streak needs updating
        original_streak = self.current_streak
        
        # If this was the first completion in a streak, reset streak to 0
        if self.current_streak == 1:
            self.current_streak = 0
            self.streak_start_date = None
        # If this was a continuation of a streak, decrement the streak count
        elif self.current_streak > 1:
            self.current_streak -= 1
        
        # Check if we need to update longest_streak
        # This happens if the current completion pushed the streak to a new record
        if self.longest_streak == original_streak and self.current_streak < self.longest_streak:
            # Find the previous longest streak (this is a simplification)
            # In a real app with streak history, you'd look up the actual previous max
            if self.current_streak > 0:
                self.longest_streak = self.current_streak
            else:
                # If we don't have historical data, we can't know for sure what the previous longest was
                # A conservative approach is to set it to 0 if current is 0
                self.longest_streak = 0
        
        # Unmark as completed
        self.is_completed = False
        
        # Update last_completed_date appropriately
        if self.current_streak > 0:
            # If we still have a streak, set last_completed_date to yesterday
            self.last_completed_date = today - timedelta(days=1)
        else:
            # If streak is reset, clear the last_completed_date
            self.last_completed_date = None
        
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

    # Add this method to the DailyHabit class
    def get_streak_info(self) -> dict:
        """
        Get detailed information about the current streak.
        
        Returns:
            dict: Streak information including start date, days completed, etc.
        """
        today = get_utc_now().date()
        
        if self.current_streak == 0:
            return {
                "current_streak": 0,
                "longest_streak": self.longest_streak,
                "streak_active": False,
                "days_since_start": 0,
                "streak_start_date": None,
                "last_completed_date": self.last_completed_date.isoformat() if self.last_completed_date else None
            }
        
        days_since_start = (today - self.streak_start_date).days + 1 if self.streak_start_date else 0
        
        return {
            "current_streak": self.current_streak,
            "longest_streak": self.longest_streak,
            "streak_active": self.is_completed and self.last_completed_date == today,
            "days_since_start": days_since_start,
            "streak_start_date": self.streak_start_date.isoformat() if self.streak_start_date else None,
            "last_completed_date": self.last_completed_date.isoformat() if self.last_completed_date else None
        }
