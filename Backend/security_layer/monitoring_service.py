"""Security monitoring service."""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from Backend.core.security.events import SecurityEventType
from Backend.data.database.repositories.security_repository import SecurityRepository
from Backend.services.notification_service.notification_service import NotificationService
from Backend.core.security.constants import (
    MAX_LOGIN_ATTEMPTS,
    LOGIN_ATTEMPT_WINDOW,
    SUSPICIOUS_IP_THRESHOLD
)


class SecurityMonitoringService:
    """Service for monitoring security events."""

    def __init__(
        self,
        db: AsyncSession,
        notification_service: NotificationService,
        background_tasks=None
    ):
        self.repository = SecurityRepository(db)
        self.notification_service = notification_service
        self.background_tasks = background_tasks

    async def check_suspicious_activity(
        self,
        ip_address: str,
        user_id: Optional[int] = None
    ) -> bool:
        """Check if current activity is suspicious."""
        # Check login attempts
        login_attempts = await self._get_recent_login_attempts(
            ip_address,
            user_id
        )
        if len(login_attempts) >= MAX_LOGIN_ATTEMPTS:
            await self._handle_excessive_login_attempts(
                ip_address,
                user_id,
                login_attempts
            )
            return True

        # Check request rate
        request_rate = await self._check_request_rate(ip_address)
        if request_rate > SUSPICIOUS_IP_THRESHOLD:
            await self._handle_suspicious_request_rate(
                ip_address,
                request_rate
            )
            return True

        return False

    async def _get_recent_login_attempts(
        self,
        ip_address: str,
        user_id: Optional[int]
    ) -> List[Any]:
        """Get recent failed login attempts."""
        since = datetime.utcnow() - timedelta(minutes=LOGIN_ATTEMPT_WINDOW)
        events = await self.repository.get_security_events(
            start_date=since,
            event_types=[SecurityEventType.LOGIN_FAILED]
        )

        return [
            e for e in events
            if (e.ip_address == ip_address or
                (user_id and e.user_id == user_id))
        ]

    async def _check_request_rate(self, ip_address: str) -> int:
        """Check request rate for IP address."""
        since = datetime.utcnow() - timedelta(minutes=1)
        events = await self.repository.get_security_events(
            start_date=since,
            event_types=["http_request"]
        )
        return len([e for e in events if e.ip_address == ip_address])

    async def _handle_excessive_login_attempts(
        self,
        ip_address: str,
        user_id: Optional[int],
        attempts: List[Any]
    ) -> None:
        """Handle excessive login attempts."""
        await self.notification_service.send_security_alert(
            title="Excessive Login Attempts Detected",
            message=(
                f"Multiple failed login attempts from IP: {ip_address}"
                f"{f' for user ID: {user_id}' if user_id else ''}"
            ),
            severity="high"
        )

    async def _handle_suspicious_request_rate(
        self,
        ip_address: str,
        rate: int
    ) -> None:
        """Handle suspicious request rate."""
        await self.notification_service.send_security_alert(
            title="Suspicious Request Rate Detected",
            message=(
                f"High request rate ({rate} requests/min) "
                f"from IP: {ip_address}"
            ),
            severity="medium"
        )

    async def analyze_security_trends(self, days: int = 7) -> Dict[str, Any]:
        """Analyze security trends over time period."""
        since = datetime.utcnow() - timedelta(days=days)
        events = await self.repository.get_security_events(
            start_date=since
        )

        return {
            "total_events": len(events),
            "events_by_type": self._group_events_by_type(events),
            "events_by_severity": self._group_events_by_severity(events),
            "top_ips": self._get_top_items(events, "ip_address"),
            "top_user_agents": self._get_top_items(events, "user_agent"),
            "suspicious_activities": self._get_suspicious_activities(events)
        }

    def _group_events_by_type(self, events: List[Any]) -> Dict[str, int]:
        """Group events by type."""
        result = {}
        for event in events:
            result[event.event_type] = result.get(event.event_type, 0) + 1
        return result

    def _group_events_by_severity(self, events: List[Any]) -> Dict[str, int]:
        """Group events by severity."""
        result = {}
        for event in events:
            result[event.severity] = result.get(event.severity, 0) + 1
        return result

    def _get_top_items(
        self,
        events: List[Any],
        field: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get top items by frequency."""
        counts = {}
        for event in events:
            value = getattr(event, field)
            if value:
                counts[value] = counts.get(value, 0) + 1

        return sorted(
            [{"value": k, "count": v} for k, v in counts.items()],
            key=lambda x: x["count"],
            reverse=True
        )[:limit]

    def _get_suspicious_activities(
        self,
        events: List[Any]
    ) -> List[Dict[str, Any]]:
        """Get suspicious activities."""
        return [
            {
                "timestamp": event.timestamp,
                "type": event.event_type,
                "description": event.description,
                "ip_address": event.ip_address,
                "metadata": event.metadata
            }
            for event in events
            if event.event_type == SecurityEventType.SUSPICIOUS_ACTIVITY
        ]
