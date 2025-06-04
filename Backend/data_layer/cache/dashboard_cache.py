import asyncio
from app.schemas.dashboard_metrics import DashboardMetrics
from data_layer.repos.focus_repo import FocusSessionRepository
from data_layer.repos.goal_repo import GoalRepository
from data_layer.repos.system_metric_repo import SystemMetricRepository
from data_layer.repos.ai_model_repo import ModelUsageRepository
from data_layer.repos.cost_tracking_repo import CostTrackingRepository
from datetime import datetime, timedelta

focus_repo = FocusSessionRepository()
goal_repo = GoalRepository()
system_repo = SystemMetricRepository()
ai_usage_repo = ModelUsageRepository()
cost_repo = CostTrackingRepository()


class DashboardCache:
    async def get_metrics(self, user_id: str):
        now = datetime.utcnow()
        last_30 = now - timedelta(days=30)
        # Fetch implemented metrics
        focus = focus_repo.get_stats(user_id)
        goals = self._get_goal_metrics(user_id)
        system = system_repo.aggregate_metrics(user_id, period="daily")
        ai_usage = ai_usage_repo.get_usage_by_user(user_id, limit=30)
        cost = await cost_repo.get_user_cost_summary(user_id, last_30, now)
        # Placeholders for not-yet-implemented metrics
        habits = None  # TODO: Implement habits aggregation
        tasks = None   # TODO: Implement tasks aggregation
        todos = None   # TODO: Implement todos aggregation
        projects = None  # TODO: Implement projects aggregation
        workflows = None  # TODO: Implement workflows aggregation
        calendar = None  # TODO: Implement calendar aggregation
        user = None      # TODO: Implement user summary aggregation
        mood = None      # TODO: Implement mood extraction from journals/notes
        shared_events = None  # TODO: Implement shared events aggregation
        notes = None     # TODO: Implement notes summary
        journals = None  # TODO: Implement journals summary
        # Compose the metrics dict as per the schema/plan
        metrics = {
            "habits": habits,
            "calendar": calendar,
            "focus": focus,
            "mood": mood,
            "ai_usage": ai_usage,
            "shared_events": shared_events,
            "system_metrics": system,
            "goals": goals,
            "tasks": tasks,
            "todos": todos,
            "projects": projects,
            "workflows": workflows,
            "user": user,
            "notes": notes,
            "journals": journals,
            "cost": cost
        }
        return metrics

    def _get_goal_metrics(self, user_id: str):
        goals = goal_repo.find_by_user(user_id)
        total = len(goals)
        completed = sum(1 for g in goals if getattr(g, 'completed', False))
        return {"total": total, "completed": completed}

    async def update(self, event):
        # Placeholder for event-driven cache update logic
        pass


dashboard_cache = DashboardCache()
