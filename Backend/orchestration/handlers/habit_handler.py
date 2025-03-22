from typing import Dict, List, Any, Optional
import logging
from Backend.orchestration.handlers.base_handler import BaseHandler
from Backend.data_layer.repositories.daily_habits_repository import DailyHabitRepository

logger = logging.getLogger(__name__)


class HabitHandler(BaseHandler):
    """
    Handler for processing habit-related queries and actions.
    """

    def __init__(self, db_session=None):
        super().__init__(db_session)
        self.repository = DailyHabitRepository(db_session)
        self.domain = "habits"

    async def get_context_data(self, user_id: int, limit: int = 10) -> Dict[str, Any]:
        """
        Retrieve habit context data for the specified user.

        Args:
            user_id: The user ID to get habits for
            limit: Maximum number of habits to retrieve

        Returns:
            Dict containing habit context data
        """
        try:
            habits = await self.repository.get_user_habits(user_id)
            habit_data = []

            # Process habits to add computed fields
            for habit in habits:
                habit_dict = habit.to_dict()
                streak_info = habit.get_streak_info()
                habit_dict.update(streak_info)
                habit_data.append(habit_dict)

            return {
                "habits": habit_data,
                "count": len(habit_data)
            }
        except Exception as e:
            logger.error(f"Error retrieving habit context: {str(e)}")
            return {"habits": [], "count": 0}
