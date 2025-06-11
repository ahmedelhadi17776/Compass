from data_layer.repos.base_repo import BaseMongoRepository
from data_layer.models.focus_model import FocusSession
from datetime import datetime, timedelta, timezone


class FocusSessionRepository(BaseMongoRepository[FocusSession]):
    def __init__(self):
        super().__init__(FocusSession)

    def find_by_user(self, user_id: str, limit: int = 100):
        return self.find_many({"user_id": user_id}, limit=limit, sort=[("start_time", -1)])

    def find_active_session(self, user_id: str):
        return self.find_one({"user_id": user_id, "status": "active"})

    def get_stats(self, user_id: str, days: int = 30):
        since = datetime.utcnow() - timedelta(days=days)
        sessions = self.find_many(
            {"user_id": user_id, "start_time": {"$gte": since}})
        total = sum((s.duration or 0)
                    for s in sessions if s.status == "completed")
        current_streak, longest_streak = self._calculate_streaks(sessions)
        return {"total_focus_seconds": total, "streak": current_streak, "longest_streak": longest_streak, "sessions": len(sessions)}

    def _calculate_streaks(self, sessions):
        """
        Returns (current_streak, longest_streak):
        - current_streak: consecutive days up to today with at least one completed session
        - longest_streak: max consecutive days with at least one completed session
        """
        # Filter only completed sessions and get their dates (in UTC, date only)
        completed_dates = set()
        for s in sessions:
            if s.status == "completed" and s.start_time:
                dt = s.start_time
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                completed_dates.add(dt.date())
        if not completed_dates:
            return 0, 0
        # Calculate current streak (ending today)
        streak = 0
        today = datetime.now(timezone.utc).date()
        while True:
            if today in completed_dates:
                streak += 1
                today = today - timedelta(days=1)
            else:
                break
        # Calculate longest streak
        all_dates = sorted(completed_dates)
        longest = 1
        current = 1
        for i in range(1, len(all_dates)):
            if (all_dates[i] - all_dates[i-1]).days == 1:
                current += 1
                if current > longest:
                    longest = current
            else:
                current = 1
        return streak, longest
