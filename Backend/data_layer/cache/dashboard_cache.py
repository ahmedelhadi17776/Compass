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
from data_layer.cache.redis_client import redis_client, redis_pubsub_client
import logging

# Define Go backend dashboard event types
class events:
    DashboardEventMetricsUpdate = "metrics_update"
    DashboardEventCacheInvalidate = "cache_invalidate"

logger = logging.getLogger(__name__)

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
        self.subscriber_task = None
        self.is_subscribed = False

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
                logger.warning(
                    f"Request to {url} failed with status {response.status}")
                return None
        except Exception as e:
            logger.error(f"Error making request to {url}: {e}")
            return None

    async def get_metrics(self, user_id: str, token: str = None):
        # Check if metrics are cached
        cache_key = f"dashboard:metrics:{user_id}"
        cached_metrics = await redis_client.get(cache_key)

        if cached_metrics:
            logger.debug(f"Cache hit for dashboard metrics: {user_id}")
            try:
                return json.loads(cached_metrics)
            except json.JSONDecodeError:
                logger.warning(
                    f"Failed to decode cached metrics for user {user_id}")
                # Continue to fetch fresh metrics

        now = datetime.utcnow()
        last_30 = now - timedelta(days=30)

        # Headers for cross-backend communication
        headers = {
            "Content-Type": "application/json",
            "X-User-ID": user_id
        }

        # Add authorization token if provided
        if token:
            headers["Authorization"] = f"Bearer {token}"

        # Fetch implemented metrics
        focus = focus_repo.get_stats(user_id)
        goals = self._get_goal_metrics(user_id)
        system = system_repo.aggregate_metrics(user_id, period="daily")
        ai_usage = ai_usage_repo.get_usage_by_user(user_id, limit=30)
        cost = await cost_repo.get_user_cost_summary(user_id, last_30, now)

        # Fetch metrics from Go backend
        go_metrics = await self._get_go_backend_metrics(user_id, headers)
        habits = go_metrics.get("data", {}).get(
            "habits") if go_metrics else None
        tasks = go_metrics.get("data", {}).get("tasks") if go_metrics else None
        todos = go_metrics.get("data", {}).get("todos") if go_metrics else None
        calendar = go_metrics.get("data", {}).get(
            "calendar") if go_metrics else None
        user_metrics = go_metrics.get("data", {}).get(
            "user") if go_metrics else None

        # Fetch metrics from Notes server
        notes_metrics = await self._get_notes_server_metrics(user_id, headers)
        mood = notes_metrics.get("mood")
        notes = notes_metrics.get("notes")
        journals = notes_metrics.get("journals")

        # Compose the metrics dict
        metrics = {
            "habits": habits,
            "calendar": calendar,
            "focus": focus,
            "mood": mood,
            "ai_usage": ai_usage,
            "system_metrics": system,
            "goals": goals,
            "tasks": tasks,
            "todos": todos,
            "user": user_metrics,
            "notes": notes,
            "journals": journals,
            "cost": cost
        }

        # Cache the results
        await self._cache_metrics(user_id, metrics)

        # Ensure we're subscribed to Go backend events
        if not self.is_subscribed:
            await self.start_go_metrics_subscriber()

        return metrics

    async def _get_go_backend_metrics(self, user_id: str, headers: dict):
        url = f"{self.go_backend_url}/api/dashboard/metrics"
        logger.debug(f"Fetching metrics from Go backend for user {user_id}")
        result = await self._make_request(url, "GET", headers)
        if not result:
            logger.warning(
                f"Failed to fetch metrics from Go backend for user {user_id}")
            # Return empty placeholders for Go backend metrics
            return {
                "data": {
                    "habits": None,
                    "tasks": None,
                    "todos": None,
                    "calendar": None,
                    "user": None
                }
            }
        else:
            logger.debug(
                f"Successfully fetched metrics from Go backend for user {user_id}")
        return result

    async def _get_notes_server_metrics(self, user_id: str, headers: dict):
        url = f"{self.notes_server_url}/api/dashboard/metrics"
        result = await self._make_request(url, "GET", headers)
        if not result:
            logger.warning(
                f"Failed to fetch metrics from Notes server for user {user_id}")
            return {}
        return result

    def _get_goal_metrics(self, user_id: str):
        goals = goal_repo.find_by_user(user_id)
        total = len(goals)
        completed = sum(1 for g in goals if getattr(g, 'completed', False))
        return {"total": total, "completed": completed}

    async def _cache_metrics(self, user_id: str, metrics: dict):
        cache_key = f"dashboard:metrics:{user_id}"
        # Cache for 5 minutes
        await redis_client.set(cache_key, json.dumps(metrics), ex=300)
        logger.debug(f"Cached dashboard metrics for user {user_id}")

    async def update(self, event: DashboardEvent):
        # Handle real-time updates
        if event.event_type == "dashboard_update":
            # Invalidate cache for this user
            cache_key = f"dashboard:metrics:{event.user_id}"
            await redis_client.delete(cache_key)
            logger.info(
                f"Invalidated dashboard cache for user {event.user_id} due to event {event.event_type}")

            # Notify subscribers
            await self._notify_subscribers(event)

    async def _notify_subscribers(self, event: DashboardEvent):
        channel = f"dashboard_updates:{event.user_id}"
        await redis_client.publish(channel, json.dumps(event.to_dict()))

    async def start_go_metrics_subscriber(self):
        """Start listening for dashboard events from Go backend"""
        if self.is_subscribed:
            return

        self.is_subscribed = True
        logger.info("Starting Go backend dashboard metrics subscriber")

        # Subscribe to the dashboard events channel
        # The Go backend uses 'dashboard:events' as the channel name
        self.subscriber_task = asyncio.create_task(
            redis_pubsub_client.subscribe(
                "dashboard:events", self._handle_go_event)
        )

    async def _handle_go_event(self, event):
        """Handle dashboard events from Go backend"""
        try:
            logger.debug(f"Received Go backend event: {event}")

            # Extract user ID from the event
            # Go backend sends a DashboardEvent with user_id as UUID
            if isinstance(event, dict) and "user_id" in event:
                # Convert UUID to string if needed
                user_id = str(event["user_id"])
                event_type = event.get("event_type", "unknown")

                logger.info(
                    f"Processing Go backend event: {event_type} for user {user_id}")

                # Invalidate cache for this user
                cache_key = f"dashboard:metrics:{user_id}"
                await redis_client.delete(cache_key)
                logger.info(
                    f"Invalidated dashboard cache for user {user_id} due to Go backend event: {event_type}")

                # If this is a metrics update event, we could potentially fetch new metrics immediately
                if event_type == events.DashboardEventMetricsUpdate:
                    logger.info(f"Metrics update event received for user {user_id}")
                    
                # Create a Python-style dashboard event and notify subscribers
                dashboard_event = DashboardEvent(
                    event_type="dashboard_update",
                    user_id=user_id,
                    entity_id=event.get("entity_id", ""),
                    details=event.get("details", {})
                )
                await self._notify_subscribers(dashboard_event)
            else:
                logger.warning(f"Received malformed Go backend event: {event}")
        except Exception as e:
            logger.error(
                f"Error handling Go backend event: {e}", exc_info=True)

    async def close(self):
        if self.subscriber_task:
            self.subscriber_task.cancel()
            try:
                await self.subscriber_task
            except asyncio.CancelledError:
                pass
            self.subscriber_task = None
            self.is_subscribed = False

        if self.session:
            await self.session.close()
            self.session = None


dashboard_cache = DashboardCache()
