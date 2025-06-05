import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
from uuid import UUID
from typing import Optional, Dict, Any
from app.schemas.dashboard_metrics import DashboardMetrics
from data_layer.repos.focus_repo import FocusSessionRepository
from data_layer.repos.goal_repo import GoalRepository
from data_layer.repos.system_metric_repo import SystemMetricRepository
from data_layer.repos.ai_model_repo import ModelUsageRepository
from data_layer.repos.cost_tracking_repo import CostTrackingRepository
from core.config import settings
from data_layer.cache.redis_client import redis_client

focus_repo = FocusSessionRepository()
goal_repo = GoalRepository()
system_repo = SystemMetricRepository()
ai_usage_repo = ModelUsageRepository()
cost_repo = CostTrackingRepository()


class DashboardEvent:
    def __init__(self, event_type: str, user_id: str, entity_id: str, details: Optional[Dict[str, Any]] = None):
        self.event_type = event_type
        self.user_id = user_id
        self.entity_id = entity_id
        self.timestamp = datetime.utcnow()
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "user_id": self.user_id,
            "entity_id": self.entity_id,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DashboardEvent':
        return cls(
            event_type=data["event_type"],
            user_id=data["user_id"],
            entity_id=data["entity_id"],
            details=data.get("details")
        )


class DashboardCache:
    def __init__(self):
        self.go_backend_url = f"http://localhost:8000"
        # Update with actual Notes server URL
        self.notes_server_url = "http://localhost:5000"
        self.session = None

    async def _get_session(self):
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session

    async def _make_request(self, url: str, method: str, headers: dict, data: dict | None = None):
        session = await self._get_session()
        try:
            async with session.request(method, url, headers=headers, json=data) as response:
                if response.status == 200:
                    return await response.json()
                return None
        except Exception as e:
            print(f"Error making request to {url}: {e}")
            return None

    async def get_metrics(self, user_id: str, token: str):
        now = datetime.utcnow()
        last_30 = now - timedelta(days=30)

        # Headers for cross-backend communication
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-User-ID": user_id
        }

        # Fetch implemented metrics
        focus = focus_repo.get_stats(user_id)
        goals = self._get_goal_metrics(user_id)
        system = system_repo.aggregate_metrics(user_id, period="daily")
        ai_usage = ai_usage_repo.get_usage_by_user(user_id, limit=30)
        cost = await cost_repo.get_user_cost_summary(user_id, last_30, now)

        # Fetch metrics from Go backend
        go_metrics = await self._get_go_backend_metrics(user_id, headers)
        habits = go_metrics.get("habits")
        tasks = go_metrics.get("tasks")
        todos = go_metrics.get("todos")
        projects = go_metrics.get("projects")
        workflows = go_metrics.get("workflows")
        calendar = go_metrics.get("calendar")
        shared_events = go_metrics.get("shared_events")

        # Fetch metrics from Notes server
        notes_metrics = await self._get_notes_server_metrics(user_id, headers)
        mood = notes_metrics.get("mood")
        notes = notes_metrics.get("notes")
        journals = notes_metrics.get("journals")

        # Fetch user metrics
        user = await self._get_user_metrics(user_id, headers)

        # Compose the metrics dict
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

        # Cache the results
        await self._cache_metrics(user_id, metrics)
        return metrics

    async def _get_go_backend_metrics(self, user_id: str, headers: dict):
        url = f"{self.go_backend_url}/api/dashboard/metrics"
        return await self._make_request(url, "GET", headers) or {}

    async def _get_notes_server_metrics(self, user_id: str, headers: dict):
        url = f"{self.notes_server_url}/api/dashboard/metrics"
        return await self._make_request(url, "GET", headers) or {}

    async def _get_user_metrics(self, user_id: str, headers: dict):
        url = f"{self.go_backend_url}/api/users/{user_id}/metrics"
        return await self._make_request(url, "GET", headers) or {}

    def _get_goal_metrics(self, user_id: str):
        goals = goal_repo.find_by_user(user_id)
        total = len(goals)
        completed = sum(1 for g in goals if getattr(g, 'completed', False))
        return {"total": total, "completed": completed}

    async def _cache_metrics(self, user_id: str, metrics: dict):
        cache_key = f"dashboard:metrics:{user_id}"
        # Cache for 5 minutes
        await redis_client.set(cache_key, json.dumps(metrics), ex=300)

    async def update(self, event: DashboardEvent):
        # Handle real-time updates
        if event.event_type == "dashboard_update":
            # Invalidate cache for this user
            cache_key = f"dashboard:metrics:{event.user_id}"
            await redis_client.delete(cache_key)

            # Notify subscribers
            await self._notify_subscribers(event)

    async def _notify_subscribers(self, event: DashboardEvent):
        channel = f"dashboard_updates:{event.user_id}"
        await redis_client.publish(channel, json.dumps(event.to_dict()))

    async def close(self):
        if self.session:
            await self.session.close()
            self.session = None


dashboard_cache = DashboardCache()
