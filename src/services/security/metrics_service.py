"""Security metrics service."""
from typing import Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from src.core.security.events import SecurityEventType
from src.data.database.repositories.security_repository import SecurityRepository
from src.core.security.exceptions import SecurityConfigError, SecurityError

logger = logging.getLogger(__name__)


class SecurityMetricsService:
    """Service for collecting and analyzing security metrics."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = SecurityRepository(db)

    async def get_metrics(self, timeframe: str) -> Dict[str, Any]:
        """Get security metrics for specified timeframe."""
        since = self._parse_timeframe(timeframe)
        events = await self.repository.get_security_events(start_date=since)

        return {
            "overview": await self._get_overview_metrics(events),
            "authentication": await self._get_auth_metrics(events),
            "threats": await self._get_threat_metrics(events),
            "performance": await self._get_performance_metrics(since)
        }

    async def _get_overview_metrics(self, events: List[Dict]) -> Dict[str, Any]:
        """Get overview metrics."""
        return {
            "total_events": len(events),
            "events_by_type": self._count_by_field(events, "event_type"),
            "events_by_severity": self._count_by_field(events, "severity"),
            "unique_ips": len(set(e["ip_address"] for e in events if e["ip_address"])),
            "unique_users": len(set(e["user_id"] for e in events if e["user_id"]))
        }

    async def _get_auth_metrics(self, events: List[Dict]) -> Dict[str, Any]:
        """Get authentication-related metrics."""
        auth_events = [
            e for e in events
            if e["event_type"] in {
                SecurityEventType.LOGIN_SUCCESS.value,
                SecurityEventType.LOGIN_FAILED.value,
                SecurityEventType.LOGOUT.value
            }
        ]

        return {
            "total_logins": len([
                e for e in auth_events
                if e["event_type"] == SecurityEventType.LOGIN_SUCCESS.value
            ]),
            "failed_logins": len([
                e for e in auth_events
                if e["event_type"] == SecurityEventType.LOGIN_FAILED.value
            ]),
            "login_success_rate": self._calculate_success_rate(auth_events),
            "unique_failed_ips": len(set(
                e["ip_address"] for e in auth_events
                if e["event_type"] == SecurityEventType.LOGIN_FAILED.value
            ))
        }

    async def _get_threat_metrics(self, events: List[Dict]) -> Dict[str, Any]:
        """Get threat-related metrics."""
        threat_events = [
            e for e in events
            if e["event_type"] in {
                SecurityEventType.SUSPICIOUS_ACTIVITY.value,
                SecurityEventType.ACCESS_DENIED.value
            }
        ]

        return {
            "total_threats": len(threat_events),
            "threats_by_type": self._count_by_field(threat_events, "event_type"),
            "threats_by_severity": self._count_by_field(threat_events, "severity"),
            "top_threat_ips": self._get_top_items(
                threat_events, "ip_address", limit=5
            )
        }

    async def _get_performance_metrics(self, since: datetime) -> Dict[str, Any]:
        """Get security performance metrics."""
        audit_logs = await self.repository.get_audit_logs(start_date=since)

        response_times = [
            float(log.details.get("duration", "0").rstrip("s"))
            for log in audit_logs
            if "duration" in log.details
        ]

        return {
            "avg_response_time": sum(response_times) / len(response_times) if response_times else 0,
            "total_requests": len(audit_logs),
            "error_rate": len([
                log for log in audit_logs
                if log.details.get("status_code", 200) >= 400
            ]) / len(audit_logs) if audit_logs else 0
        }

    @staticmethod
    def _parse_timeframe(timeframe: str) -> datetime:
        """Parse timeframe string into datetime."""
        now = datetime.utcnow()

        if timeframe == "24h":
            return now - timedelta(hours=24)
        elif timeframe == "7d":
            return now - timedelta(days=7)
        elif timeframe == "30d":
            return now - timedelta(days=30)
        else:
            return now - timedelta(hours=24)  # Default to 24h

    @staticmethod
    def _count_by_field(events: List[Dict], field: str) -> Dict[str, int]:
        """Count events by specified field."""
        counts = {}
        for event in events:
            value = event.get(field)
            if value:
                counts[value] = counts.get(value, 0) + 1
        return counts

    @staticmethod
    def _calculate_success_rate(auth_events: List[Dict]) -> float:
        """Calculate login success rate."""
        total = len([
            e for e in auth_events
            if e["event_type"] in {
                SecurityEventType.LOGIN_SUCCESS.value,
                SecurityEventType.LOGIN_FAILED.value
            }
        ])

        if not total:
            return 0.0

        successes = len([
            e for e in auth_events
            if e["event_type"] == SecurityEventType.LOGIN_SUCCESS.value
        ])

        return (successes / total) * 100

    @staticmethod
    def _get_top_items(events: List[Dict], field: str, limit: int) -> List[Dict[str, Any]]:
        """Get top items by count for specified field."""
        counts = {}
        for event in events:
            value = event.get(field)
            if value:
                counts[value] = counts.get(value, 0) + 1

        return sorted(
            [{"value": k, "count": v} for k, v in counts.items()],
            key=lambda x: x["count"],
            reverse=True
        )[:limit]
