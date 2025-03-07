from Backend.data_layer.repositories.daily_habits_repository import DailyHabitRepository
from Backend.data_layer.database.models.daily_habits import DailyHabit
from Backend.data_layer.cache.redis_client import get_cached_value, set_cached_value, delete_cached_value
from typing import Optional, List, Dict, Any, cast
from datetime import datetime, date, timedelta
import json
import logging

logger = logging.getLogger(__name__)


class DailyHabitService:
    """Service for managing daily habits with streak tracking."""

    def __init__(self, repository: DailyHabitRepository):
        self.repository = repository
        self.cache_ttl = 3600  # 1 hour cache

    async def _get_from_cache_or_db(self, cache_key: str, db_func, ttl: Optional[int] = None) -> Any:
        """Generic method to handle get operations with caching."""
        cached_data = await get_cached_value(cache_key)
        if cached_data:
            try:
                data = json.loads(cached_data)
                if isinstance(data, list):
                    return [h for h in (DailyHabit.from_dict(h) for h in data) if h is not None]
                return DailyHabit.from_dict(data)
            except Exception as e:
                logger.error(f"Error deserializing cached data: {e}")

        result = await db_func()
        if result:
            try:
                data = [h.to_dict() for h in result] if isinstance(
                    result, list) else result.to_dict()
                await set_cached_value(cache_key, json.dumps(data), ttl or self.cache_ttl)
            except Exception as e:
                logger.error(f"Error caching data: {e}")

        return result

    async def get_habit_by_id(self, habit_id: int, user_id: int) -> Optional[DailyHabit]:
        """Get a habit by ID."""
        return await self._get_from_cache_or_db(
            f"habit:{habit_id}:{user_id}",
            lambda: self.repository.get_by_id(habit_id, user_id)
        )

    async def get_user_habits(self, user_id: int) -> List[DailyHabit]:
        """Get all habits for a user."""
        return await self._get_from_cache_or_db(
            f"user_habits:{user_id}",
            lambda: self.repository.get_user_habits(user_id)
        )

    async def get_active_habits(self, user_id: int) -> List[DailyHabit]:
        """Get all active habits for a user."""
        return await self._get_from_cache_or_db(
            f"active_habits:{user_id}",
            lambda: self.repository.get_active_habits(user_id)
        )

    async def get_habits_due_today(self, user_id: int) -> List[DailyHabit]:
        """Get habits that are active today but not yet completed."""
        return await self._get_from_cache_or_db(
            f"habits_due_today:{user_id}",
            lambda: self.repository.get_habits_due_today(user_id),
            300  # 5 minutes TTL
        )

    async def get_top_streaks(self, user_id: int, limit: int = 5) -> List[DailyHabit]:
        """Get habits with the highest current streaks."""
        return await self._get_from_cache_or_db(
            f"top_streaks:{user_id}:{limit}",
            lambda: self.repository.get_top_streaks(user_id, limit)
        )

    async def _db_operation(self, operation, user_id: int, habit_id: Optional[int] = None) -> Any:
        """Generic method to handle database operations with transaction and cache management."""
        try:
            result = await operation()
            await self.repository.db.commit()
            if result:
                await self._invalidate_cache(user_id, habit_id)
            return result
        except Exception as e:
            await self.repository.db.rollback()
            logger.error(f"Error in database operation: {e}")
            raise

    async def create_habit(self, **habit_data) -> Optional[DailyHabit]:
        """Create a new daily habit."""
        return await self._db_operation(
            lambda: self.repository.create(**habit_data),
            cast(int, habit_data.get('user_id'))
        )

    async def update_habit(self, habit_id: int, user_id: int, **update_data) -> Optional[DailyHabit]:
        """Update a habit."""
        return await self._db_operation(
            lambda: self.repository.update(habit_id, user_id, **update_data),
            user_id, habit_id
        )

    async def delete_habit(self, habit_id: int, user_id: int) -> bool:
        """Delete a habit."""
        return await self._db_operation(
            lambda: self.repository.delete(habit_id, user_id),
            user_id, habit_id
        )

    async def mark_habit_completed(self, habit_id: int, user_id: int) -> Optional[DailyHabit]:
        """Mark a habit as completed for today and update streak."""
        return await self._db_operation(
            lambda: self.repository.mark_habit_completed(habit_id, user_id),
            user_id, habit_id
        )

    async def _invalidate_all_caches(self) -> None:
        """Invalidate all habit-related caches globally."""
        try:
            patterns = [
                "habit:*",
                "user_habits:*",
                "active_habits:*",
                "habits_due_today:*",
                "top_streaks:*"
            ]
            for pattern in patterns:
                await delete_cached_value(pattern)
        except Exception as e:
            logger.error(f"Error invalidating all caches: {e}")

    async def process_daily_reset(self) -> Dict[str, int]:
        """
        Process daily reset operations:
        1. Reset completion status for all habits
        2. Check and reset broken streaks

        This should be called once per day, typically at midnight.

        Returns:
            Dict with counts of habits affected
        """
        try:
            # First invalidate all caches to ensure fresh data
            await self._invalidate_all_caches()

            # Reset all daily completions
            reset_count = await self.repository.reset_daily_completions()

            # Check and reset broken streaks
            streak_reset_count = await self.repository.check_and_reset_broken_streaks()

            # Commit the changes
            await self.repository.db.commit()

            # Invalidate all caches again after changes
            await self._invalidate_all_caches()

            return {
                "completions_reset": reset_count,
                "streaks_reset": streak_reset_count
            }
        except Exception as e:
            # Rollback on error
            await self.repository.db.rollback()
            logger.error(f"Error during daily reset: {e}")
            raise

    async def _invalidate_cache(self, user_id: int, habit_id: Optional[int] = None) -> None:
        """Invalidate habit-related caches for a specific user."""
        try:
            # Invalidate specific habit cache if habit_id is provided
            if habit_id:
                await delete_cached_value(f"habit:{habit_id}:{user_id}")

            # Invalidate user's habit lists
            patterns = [
                f"user_habits:{user_id}",
                f"active_habits:{user_id}",
                f"habits_due_today:{user_id}",
                f"top_streaks:{user_id}:*"
            ]
            for pattern in patterns:
                await delete_cached_value(pattern)
        except Exception as e:
            # Log cache invalidation errors but don't fail the operation
            logger.error(f"Error invalidating cache: {e}")
