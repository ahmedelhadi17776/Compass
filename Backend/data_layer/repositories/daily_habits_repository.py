from Backend.data_layer.database.models.daily_habits import DailyHabit
from Backend.data_layer.repositories.base_repository import BaseRepository
from sqlalchemy.future import select
from sqlalchemy import and_, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
import logging

logger = logging.getLogger(__name__)


class DailyHabitRepository(BaseRepository[DailyHabit]):
    """Repository for managing daily habits with streak tracking."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, **habit_data) -> DailyHabit:
        """Create a new daily habit."""
        habit = DailyHabit(**habit_data)
        self.db.add(habit)
        await self.db.flush()
        return habit

    async def get_by_id(self, id: int, user_id: Optional[int] = None) -> Optional[DailyHabit]:
        """Get a daily habit by ID with optional user filtering."""
        query = select(DailyHabit).where(DailyHabit.id == id)

        if user_id is not None:
            query = query.where(DailyHabit.user_id == user_id)

        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_user_habits(self, user_id: int) -> List[DailyHabit]:
        """Get all habits for a specific user."""
        query = select(DailyHabit).where(DailyHabit.user_id == user_id)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_active_habits(self, user_id: int) -> List[DailyHabit]:
        """Get all active habits (within start and end dates) for a user."""
        today = date.today()
        query = select(DailyHabit).where(
            and_(
                DailyHabit.user_id == user_id,
                DailyHabit.start_day <= today,
                (DailyHabit.end_day.is_(None) | (DailyHabit.end_day >= today))
            )
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def update(self, id: int, user_id: int, **update_data) -> Optional[DailyHabit]:
        """Update a daily habit."""
        habit = await self.get_by_id(id, user_id)
        if not habit:
            return None

        for key, value in update_data.items():
            if hasattr(habit, key):
                setattr(habit, key, value)

        await self.db.flush()
        return habit

    async def delete(self, id: int, user_id: int) -> bool:
        """Delete a daily habit."""
        stmt = delete(DailyHabit).where(
            and_(
                DailyHabit.id == id,
                DailyHabit.user_id == user_id
            )
        )
        result = await self.db.execute(stmt)
        return result.rowcount > 0

    async def mark_habit_completed(self, id: int, user_id: int, completion_date: Optional[date] = None) -> Optional[DailyHabit]:
        """Mark a habit as completed for today and update streak."""
        habit = await self.get_by_id(id, user_id)
        if not habit:
            return None

        habit.mark_completed(completion_date)
        await self.db.flush()
        return habit

    async def reset_daily_completions(self) -> int:
        """
        Reset all daily completions without affecting streaks.
        Called at the end of the day (e.g., midnight).

        Returns:
            int: Number of habits reset
        """
        stmt = update(DailyHabit).where(
            DailyHabit.is_completed == True).values(is_completed=False)
        result = await self.db.execute(stmt)
        return result.rowcount

    async def check_and_reset_broken_streaks(self) -> int:
        """
        Check all habits and reset streaks for those that missed a day.
        Called at the end of the day (e.g., midnight).

        Returns:
            int: Number of streaks reset
        """
        today = date.today()
        yesterday = today - timedelta(days=1)

        # Find habits that were not completed yesterday and have a streak > 0
        query = select(DailyHabit).where(
            and_(
                DailyHabit.current_streak > 0,
                (DailyHabit.last_completed_date.is_(None) |
                 (DailyHabit.last_completed_date < yesterday))
            )
        )

        result = await self.db.execute(query)
        habits_to_reset = result.scalars().all()

        # Reset streaks for these habits
        reset_count = 0
        for habit in habits_to_reset:
            if habit.check_streak_reset():
                reset_count += 1

        await self.db.flush()
        return reset_count

    async def get_top_streaks(self, user_id: int, limit: int = 5) -> List[DailyHabit]:
        """Get habits with the highest current streaks for a user."""
        query = select(DailyHabit).where(
            DailyHabit.user_id == user_id
        ).order_by(DailyHabit.current_streak.desc()).limit(limit)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_habits_due_today(self, user_id: int) -> List[DailyHabit]:
        """Get habits that are active today but not yet completed."""
        today = date.today()
        query = select(DailyHabit).where(
            and_(
                DailyHabit.user_id == user_id,
                DailyHabit.start_day <= today,
                (DailyHabit.end_day.is_(None) | (DailyHabit.end_day >= today)),
                DailyHabit.is_completed == False
            )
        )

        result = await self.db.execute(query)
        return result.scalars().all()
