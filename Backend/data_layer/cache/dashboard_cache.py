import asyncio
import aiohttp
import json
import time
from datetime import datetime, timedelta
from uuid import UUID
from typing import Optional, Dict, Any, List, Tuple
from app.schemas.dashboard_metrics import DashboardMetrics
from data_layer.repos.focus_repo import FocusSessionRepository
from data_layer.repos.goal_repo import GoalRepository
from data_layer.repos.system_metric_repo import SystemMetricRepository
from data_layer.repos.ai_model_repo import ModelUsageRepository
from data_layer.repos.cost_tracking_repo import CostTrackingRepository
from core.config import settings
from data_layer.cache.redis_client import redis_client, redis_pubsub_client
import logging
import os
from data_layer.cache.pubsub_manager import PubSubManager

# Import WebSocket manager
try:
    from api.websocket.dashboard_ws import dashboard_ws_manager
except ImportError:
    dashboard_ws_manager = None
    logging.getLogger(__name__).warning(
        "WebSocket manager not available, real-time updates will be disabled")

# Define Go backend dashboard event types
class events:
    DashboardEventMetricsUpdate = "metrics_update"
    DashboardEventCacheInvalidate = "cache_invalidate"

# Custom error classes for better error handling
class DashboardError(Exception):
    def __init__(self, message, error_type, details=None):
        super().__init__(message)
        self.error_type = error_type
        self.details = details or {}

class DashboardMetricsError(DashboardError):
    pass

class CircuitBreaker:
    """Circuit breaker pattern implementation to prevent cascading failures"""
    
    def __init__(self, failure_threshold=5, reset_timeout=60, name="default"):
        self._failure_count = 0
        self._failure_threshold = failure_threshold
        self._reset_timeout = reset_timeout
        self._last_failure_time = 0
        self._is_open = False
        self.name = name
    
    @property
    def is_open(self):
        """Check if circuit is open"""
        return self._is_open
    
    @property
    def failure_count(self):
        """Get current failure count"""
        return self._failure_count
    
    @property
    def last_failure_time(self):
        """Get last failure timestamp"""
        return self._last_failure_time
        
    async def execute(self, func, *args, **kwargs):
        if self._is_open:
            if time.time() - self._last_failure_time > self._reset_timeout:
                self._is_open = False
            else:
                raise DashboardError(
                    "Circuit breaker is open", 
                    "circuit_open", 
                    {"reset_in": self._reset_timeout - (time.time() - self._last_failure_time)}
                )
                
        try:
            result = await func(*args, **kwargs)
            self._failure_count = 0
            return result
        except Exception as e:
            self._failure_count += 1
            if self._failure_count >= self._failure_threshold:
                self._is_open = True
                self._last_failure_time = time.time()
            raise


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
        self.redis_client = redis_client
        self.pubsub_manager = PubSubManager()
        self.is_subscribed = False
        self.notes_server_url = f"http://localhost:5000"
        self.session = None
        self.subscriber_task = None
        # Store reference to WebSocket manager if available
        self.ws_manager = dashboard_ws_manager
        # In-memory cache for faster access
        self._memory_cache = {}
        # Cache lock to prevent race conditions
        self._cache_lock = asyncio.Lock()
        # Circuit breakers for external services
        self._go_backend_circuit = CircuitBreaker(failure_threshold=3, reset_timeout=30)
        self._notes_server_circuit = CircuitBreaker(failure_threshold=3, reset_timeout=30)
        # Metrics collection
        self._metrics = {
            "cache_hits": 0,
            "cache_misses": 0,
            "memory_cache_hits": 0,
            "memory_cache_misses": 0,
            "fetch_times": [],
            "errors": 0
        }

    async def _get_session(self):
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session

    async def _make_request(self, url, method, headers=None, data=None, timeout=10.0):
        """Make HTTP request to external service with timeout"""
        session = await self._get_session()
        try:
            async with session.request(method, url, headers=headers, json=data, timeout=timeout) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.warning(f"Request to {url} failed with status {response.status}")
                    return None
        except asyncio.TimeoutError:
            logger.warning(f"Request to {url} timed out after {timeout} seconds")
            raise DashboardError(f"Request to {url} timed out")
        except Exception as e:
            logger.error(f"Error making request to {url}: {str(e)}")
            raise DashboardError(f"Error making request to {url}: {str(e)}")
            
    async def _get_focus_metrics(self, user_id: str):
        """Fetch focus metrics asynchronously"""
        try:
            focus_repo = FocusSessionRepository()
            return await focus_repo.get_focus_statistics(user_id, days=30)
        except Exception as e:
            logger.error(f"Error fetching focus metrics: {str(e)}")
            return {}
            
    async def _get_goal_metrics_async(self, user_id: str):
        """Fetch goal metrics asynchronously"""
        try:
            goal_repo = GoalRepository()
            goals = await goal_repo.find_by_user(user_id)
            return await self._calculate_goal_metrics(goals)
        except Exception as e:
            logger.error(f"Error fetching goal metrics: {str(e)}")
            return {}
            
    async def _get_system_metrics(self, user_id: str):
        """Fetch system metrics asynchronously"""
        try:
            system_metrics_repo = SystemMetricsRepository()
            return await system_metrics_repo.get_system_metrics(user_id)
        except Exception as e:
            logger.error(f"Error fetching system metrics: {str(e)}")
            return {}
            
    async def _get_ai_usage_metrics(self, user_id: str):
        """Fetch AI usage metrics asynchronously"""
        try:
            ai_usage_repo = AIUsageRepository()
            return await ai_usage_repo.get_usage_statistics(user_id, days=30)
        except Exception as e:
            logger.error(f"Error fetching AI usage metrics: {str(e)}")
            return {}

    async def get_metrics(self, user_id: str, token: str = ""):
        start_time = time.time()
        
        try:
            # Check memory cache first (1-second threshold)
            if user_id in self._memory_cache:
                metrics, timestamp = self._memory_cache[user_id]
                if time.time() - timestamp < 1:  # 1 second threshold
                    logger.debug(f"Memory cache hit for dashboard metrics: {user_id}")
                    self._metrics["cache_hits"] += 1
                    return metrics
            
            # Check Redis cache
            cache_key = f"dashboard:metrics:{user_id}"
            cached_metrics = await redis_client.get(cache_key)

            if cached_metrics:
                logger.debug(f"Redis cache hit for dashboard metrics: {user_id}")
                self._metrics["cache_hits"] += 1
                try:
                    metrics = json.loads(cached_metrics)
                    # Update memory cache
                    self._memory_cache[user_id] = (metrics, time.time())
                    return metrics
                except json.JSONDecodeError:
                    logger.warning(f"Failed to decode cached metrics for user {user_id}")
                    # Continue to fetch fresh metrics
            
            # Cache miss, fetch fresh metrics
            self._metrics["cache_misses"] += 1
            logger.debug(f"Cache miss for dashboard metrics: {user_id}")
            
            metrics = await self._fetch_all_metrics(user_id, token)
            
            # Cache the results
            await self._cache_metrics(user_id, metrics)
            
            # Update memory cache
            self._memory_cache[user_id] = (metrics, time.time())
            
            # Ensure we're subscribed to Go backend events
            if not self.is_subscribed:
                await self.start_go_metrics_subscriber()
            
            # Record fetch time
            fetch_time = (time.time() - start_time) * 1000  # Convert to ms
            self._metrics["fetch_times"].append(fetch_time)
            
            return metrics
            
        except Exception as e:
            self._metrics["errors"] += 1
            logger.error(f"Error getting dashboard metrics: {str(e)}")
            raise DashboardMetricsError(
                str(e),
                "fetch_error",
                {"user_id": user_id}
            )

    async def _fetch_all_metrics(self, user_id: str, token: str = ""):
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

        # Create tasks for concurrent fetching
        # Local database metrics
        focus_task = asyncio.create_task(self._get_focus_metrics(user_id))
        goals_task = asyncio.create_task(self._get_goal_metrics_async(user_id))
        system_task = asyncio.create_task(self._get_system_metrics(user_id))
        ai_usage_task = asyncio.create_task(self._get_ai_usage_metrics(user_id))
        cost_task = asyncio.create_task(cost_repo.get_user_cost_summary(user_id, last_30, now))
        
        # External services metrics
        go_metrics_task = asyncio.create_task(self._get_go_backend_metrics(user_id, headers))
        notes_metrics_task = asyncio.create_task(self._get_notes_server_metrics(user_id, headers))
        
        # Wait for all tasks to complete with timeout
        try:
            # First, wait for local metrics (these should be fast)
            focus, goals, system, ai_usage, cost = await asyncio.gather(
                focus_task, goals_task, system_task, ai_usage_task, cost_task,
                return_exceptions=True
            )
            
            # Then, wait for external metrics with timeout
            go_metrics, notes_metrics = await asyncio.wait_for(
                asyncio.gather(go_metrics_task, notes_metrics_task, return_exceptions=True),
                timeout=5.0
            )
            
            # Extract Go backend metrics
            if isinstance(go_metrics, Exception):
                logger.error(f"Error fetching Go backend metrics: {str(go_metrics)}")
                habits, tasks, todos, calendar, user_metrics = None, None, None, None, None
            else:
                habits = go_metrics.get("data", {}).get("habits") if go_metrics else None
                tasks = go_metrics.get("data", {}).get("tasks") if go_metrics else None
                todos = go_metrics.get("data", {}).get("todos") if go_metrics else None
                calendar = go_metrics.get("data", {}).get("calendar") if go_metrics else None
                user_metrics = go_metrics.get("data", {}).get("user") if go_metrics else None
            
            # Extract Notes server metrics
            if isinstance(notes_metrics, Exception):
                logger.error(f"Error fetching Notes server metrics: {str(notes_metrics)}")
                mood, notes, journals = None, None, None
            else:
                mood = notes_metrics.get("mood") if notes_metrics else None
                notes = notes_metrics.get("notes") if notes_metrics else None
                journals = notes_metrics.get("journals") if notes_metrics else None
            
            # Handle exceptions in local metrics
            focus = None if isinstance(focus, Exception) else focus
            goals = None if isinstance(goals, Exception) else goals
            system = None if isinstance(system, Exception) else system
            ai_usage = None if isinstance(ai_usage, Exception) else ai_usage
            cost = None if isinstance(cost, Exception) else cost
            
        except asyncio.TimeoutError:
            logger.error(f"Timeout fetching external metrics for user {user_id}")
            # Use None for external metrics that timed out
            habits, tasks, todos, calendar, user_metrics = None, None, None, None, None
            mood, notes, journals = None, None, None
            
            # Try to get results from tasks that might have completed
            if go_metrics_task.done() and not go_metrics_task.exception():
                go_metrics = go_metrics_task.result()
                habits = go_metrics.get("data", {}).get("habits") if go_metrics else None
                tasks = go_metrics.get("data", {}).get("tasks") if go_metrics else None
                todos = go_metrics.get("data", {}).get("todos") if go_metrics else None
                calendar = go_metrics.get("data", {}).get("calendar") if go_metrics else None
                user_metrics = go_metrics.get("data", {}).get("user") if go_metrics else None
                
            if notes_metrics_task.done() and not notes_metrics_task.exception():
                notes_metrics = notes_metrics_task.result()
                mood = notes_metrics.get("mood") if notes_metrics else None
                notes = notes_metrics.get("notes") if notes_metrics else None
                journals = notes_metrics.get("journals") if notes_metrics else None
        
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
        
        return metrics
        
    async def _get_focus_metrics(self, user_id: str):
        """Get focus metrics from local database"""
        return focus_repo.get_stats(user_id)
        
    async def _get_goal_metrics_async(self, user_id: str):
        """Async wrapper for goal metrics"""
        return self._get_goal_metrics(user_id)
        
    async def _get_system_metrics(self, user_id: str):
        """Get system metrics from local database"""
        return system_repo.aggregate_metrics(user_id, period="daily")
        
    async def _get_ai_usage_metrics(self, user_id: str):
        """Get AI usage metrics from local database"""
        return ai_usage_repo.get_usage_by_user(user_id, limit=30)

    async def _get_go_backend_metrics(self, user_id: str, headers: dict):
        """Fetch metrics from Go backend with circuit breaker"""
        url = f"{self.go_backend_url}/api/dashboard/metrics"
        logger.debug(f"Fetching metrics from Go backend for user {user_id}")
        
        try:
            # Use circuit breaker to prevent cascading failures
            result = await self._go_backend_circuit.execute(
                self._make_request,
                url, "GET", headers, None, 3.0  # 3 second timeout
            )
            
            if not result:
                logger.warning(f"Failed to fetch metrics from Go backend for user {user_id}")
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
                logger.debug(f"Successfully fetched metrics from Go backend for user {user_id}")
            return result
            
        except DashboardError as e:
            # Circuit breaker is open
            logger.error(f"Circuit breaker open for Go backend: {e}")
            return {
                "data": {
                    "habits": None,
                    "tasks": None,
                    "todos": None,
                    "calendar": None,
                    "user": None
                }
            }
        except Exception as e:
            logger.error(f"Unexpected error fetching Go backend metrics: {e}")
            return {
                "data": {
                    "habits": None,
                    "tasks": None,
                    "todos": None,
                    "calendar": None,
                    "user": None
                }
            }

    async def _get_notes_server_metrics(self, user_id: str, headers: dict):
        """Fetch metrics from Notes server with circuit breaker"""
        try:
            # Use circuit breaker to prevent cascading failures
            url = f"{self.notes_server_url}/api/dashboard/metrics"
            response = await self._notes_server_circuit.execute(
                self._make_request,
                url, "GET", headers, None, 3.0  # 3 second timeout
            )
            
            if response and response.get("success"):
                data = response.get("data", {})
                logger.info(f"Successfully fetched Notes server metrics for user {user_id}")
                return {
                    "mood": data.get("moodSummary"),
                    "notes": {
                        "count": data.get("notesCount", 0),
                        "recent": data.get("recentNotes", []),
                        "tags": data.get("tagCounts", [])
                    },
                    "journals": {
                        "count": data.get("journalsCount", 0),
                        "recent": data.get("recentJournals", []),
                        "mood_distribution": data.get("moodDistribution", {})
                    }
                }
            logger.warning(f"Failed to fetch metrics from Notes server for user {user_id}")
            return {
                "mood": None,
                "notes": None,
                "journals": None
            }
        except DashboardError as e:
            # Circuit breaker is open
            logger.error(f"Circuit breaker open for Notes server: {e}")
            return {
                "mood": None,
                "notes": None,
                "journals": None
            }
        except Exception as e:
            logger.error(f"Error fetching Notes server metrics: {str(e)}")
            return {
                "mood": None,
                "notes": None,
                "journals": None
            }

    def _get_goal_metrics(self, user_id: str):
        goals = goal_repo.find_by_user(user_id)
        total = len(goals)
        completed = sum(1 for g in goals if getattr(g, 'completed', False))
        return {"total": total, "completed": completed}

    async def _cache_metrics(self, user_id: str, metrics: dict):
        """Cache metrics with TTL and update memory cache"""
        cache_key = f"dashboard:metrics:{user_id}"
        # Cache for 5 minutes in Redis
        await redis_client.set(cache_key, json.dumps(metrics), ex=300)
        # Update memory cache
        self._memory_cache[user_id] = (metrics, time.time())
        logger.debug(f"Cached dashboard metrics for user {user_id}")
        
    async def update_metric(self, user_id: str, metric_type: str, value: Any):
        """Update a specific metric in the cache without invalidating the entire cache"""
        async with self._cache_lock:
            # Get current metrics
            cache_key = f"dashboard:metrics:{user_id}"
            cached_metrics = await redis_client.get(cache_key)
            
            if not cached_metrics:
                logger.warning(f"Cannot update metric {metric_type} for user {user_id}: cache miss")
                return False
                
            try:
                current_metrics = json.loads(cached_metrics)
                # Update specific metric
                current_metrics[metric_type] = value
                
                # Update Redis cache
                await redis_client.set(cache_key, json.dumps(current_metrics), ex=300)
                
                # Update memory cache
                self._memory_cache[user_id] = (current_metrics, time.time())
                
                logger.debug(f"Updated metric {metric_type} for user {user_id}")
                return True
            except (json.JSONDecodeError, KeyError) as e:
                logger.error(f"Error updating metric {metric_type}: {str(e)}")
                return False

    async def invalidate_cache(self, user_id: str):
        """Invalidate the cache for a specific user"""
        cache_key = f"dashboard:metrics:{user_id}"
        # Remove from Redis cache
        await redis_client.delete(cache_key)
        # Remove from memory cache
        if user_id in self._memory_cache:
            del self._memory_cache[user_id]
        logger.info(f"Invalidated dashboard cache for user {user_id}")

        # Create an event to notify subscribers
        event = DashboardEvent(
            event_type="cache_invalidate",
            user_id=user_id,
            entity_id="",
            details={"timestamp": datetime.utcnow().isoformat()}
        )
        await self._notify_subscribers(event)

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
        # Publish to Redis channel for other services
        channel = f"dashboard_updates:{event.user_id}"
        await redis_client.publish(channel, json.dumps(event.to_dict()))

        # Broadcast to WebSocket clients if WebSocket manager is available
        if self.ws_manager:
            # Add metrics to the event if it's a cache invalidation
            if event.event_type == "cache_invalidate":
                # Check if we have metrics in memory cache to avoid loading delay
                if event.user_id in self._memory_cache:
                    metrics, _ = self._memory_cache[event.user_id]
                    # Include metrics in the WebSocket message to avoid client having to fetch them
                    message = {
                        "type": event.event_type,
                        "timestamp": datetime.utcnow().isoformat(),
                        "data": event.details,
                        "metrics": metrics
                    }
                    await self.ws_manager.broadcast_to_user(event.user_id, message)
                    logger.debug(f"Sent dashboard update with metrics to WebSocket for user {event.user_id}")
                    return
            
            # Default case without metrics
            message = {
                "type": event.event_type,
                "timestamp": datetime.utcnow().isoformat(),
                "data": event.details
            }
            await self.ws_manager.broadcast_to_user(event.user_id, message)
            logger.debug(f"Broadcasted event to WebSocket clients for user {event.user_id}")

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
                    logger.info(
                        f"Metrics update event received for user {user_id}")

                # Create a Python-style dashboard event and notify subscribers
                dashboard_event = DashboardEvent(
                    event_type=event_type,
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

    async def _handle_notes_event(self, event):
        """Handle events from Notes server"""
        try:
            logger.debug(f"Received Notes server event: {event}")

            if isinstance(event, dict) and "user_id" in event:
                user_id = str(event["user_id"])
                event_type = event.get("event_type", "unknown")
                details = event.get("details", {})

                logger.info(
                    f"Processing Notes server event: {event_type} for user {user_id}")

                # Invalidate cache for this user
                cache_key = f"dashboard:metrics:{user_id}"
                await self.redis_client.delete(cache_key)
                logger.info(
                    f"Invalidated dashboard cache for user {user_id} due to Notes server event: {event_type}")

                # If this is a metrics update event, we could potentially fetch new metrics immediately
                if event_type == events.DashboardEventMetricsUpdate:
                    logger.info(
                        f"Metrics update event received for user {user_id}")
                    # Fetch fresh metrics
                    headers = {"X-User-ID": user_id}
                    metrics = await self._get_notes_server_metrics(user_id, headers)
                    if metrics:
                        await self._cache_metrics(user_id, metrics)

                # Create a Python-style dashboard event and notify subscribers
                dashboard_event = DashboardEvent(
                    event_type=event_type,
                    user_id=user_id,
                    entity_id=event.get("entity_id", ""),
                    details=details
                )
                await self._notify_subscribers(dashboard_event)
            else:
                logger.warning(
                    f"Received malformed Notes server event: {event}")
        except Exception as e:
            logger.error(
                f"Error handling Notes server event: {e}", exc_info=True)

    async def start_notes_metrics_subscriber(self):
        """Start subscriber for Notes server events"""
        if self.is_subscribed:
            return

        self.is_subscribed = True
        logger.info("Starting Notes server dashboard metrics subscriber")

        # Subscribe to the dashboard events channel
        self.subscriber_task = asyncio.create_task(
            redis_pubsub_client.subscribe(
                "dashboard:events", self._handle_notes_event)
        )

    def get_metrics_statistics(self):
        """Get statistics about dashboard metrics for monitoring"""
        stats = {
            "cache_hit_rate": 0,
            "memory_cache_hit_rate": 0,
            "avg_fetch_time_ms": 0,
            "error_rate": 0,
            "memory_cache_size": len(self._memory_cache),
            "circuit_breaker_status": {
                "go_backend": {
                    "state": "open" if self._go_backend_circuit.is_open else "closed",
                    "failure_count": self._go_backend_circuit.failure_count,
                    "last_failure": self._go_backend_circuit.last_failure_time
                },
                "notes_server": {
                    "state": "open" if self._notes_server_circuit.is_open else "closed",
                    "failure_count": self._notes_server_circuit.failure_count,
                    "last_failure": self._notes_server_circuit.last_failure_time
                }
            }
        }
        
        # Calculate cache hit rates
        total_redis_requests = self._metrics["cache_hits"] + self._metrics["cache_misses"]
        if total_redis_requests > 0:
            stats["cache_hit_rate"] = self._metrics["cache_hits"] / total_redis_requests
            
        total_memory_requests = self._metrics["memory_cache_hits"] + self._metrics["memory_cache_misses"]
        if total_memory_requests > 0:
            stats["memory_cache_hit_rate"] = self._metrics["memory_cache_hits"] / total_memory_requests
        
        # Calculate average fetch time
        if self._metrics["fetch_times"]:
            stats["avg_fetch_time_ms"] = sum(self._metrics["fetch_times"]) / len(self._metrics["fetch_times"])
        
        # Calculate error rate (errors per 100 requests)
        total_requests = total_redis_requests
        if total_requests > 0:
            stats["error_rate"] = (self._metrics["errors"] / total_requests) * 100
            
        return stats

    async def close(self):
        """Cleanup resources"""
        if self.is_subscribed:
            await self.pubsub_manager.unsubscribe()
            self.is_subscribed = False
            logger.info("Unsubscribed from Notes server dashboard events")

        if self.subscriber_task:
            self.subscriber_task.cancel()
            try:
                await self.subscriber_task
            except asyncio.CancelledError:
                pass
            self.subscriber_task = None

        if self.session:
            await self.session.close()
            self.session = None


dashboard_cache = DashboardCache()
