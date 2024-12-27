"""Security monitoring service."""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from fastapi import BackgroundTasks

from src.core.security.events import SecurityEventType
from src.data.database.repositories.security_repository import SecurityRepository
from src.services.notification_service.notification_service import NotificationService

logger = logging.getLogger(__name__)


class SecurityMonitoringService:
    """Service for security monitoring and alerts."""

    def __init__(
        self,
        db: AsyncSession,
        notification_service: NotificationService,
        background_tasks: BackgroundTasks
    ):
        self.db = db
        self.repository = SecurityRepository(db)
        self.notification_service = notification_service
        self.background_tasks = background_tasks

    async def check_suspicious_activities(self, timeframe_minutes: int = 5) -> None:
        """Check for suspicious activities in recent timeframe."""
        since = datetime.utcnow() - timedelta(minutes=timeframe_minutes)

        # Get recent security events
        events = await self.repository.get_security_events(
            start_date=since,
            event_types=[
                SecurityEventType.LOGIN_FAILED,
                SecurityEventType.ACCESS_DENIED,
                SecurityEventType.SUSPICIOUS_ACTIVITY
            ]
        )

        # Analyze events by IP
        ip_activities = self._analyze_ip_activities(events)

        # Check for suspicious patterns
        for ip, data in ip_activities.items():
            if self._is_suspicious_activity(data):
                await self._handle_suspicious_ip(ip, data)

    async def monitor_authentication_failures(self) -> None:
        """Monitor for authentication failures."""
        # Get recent failed login attempts
        events = await self.repository.get_security_events(
            event_types=[SecurityEventType.LOGIN_FAILED],
            limit=100
        )

        # Group by user and IP
        failures_by_user = self._group_failures_by_user(events)
        failures_by_ip = self._group_failures_by_ip(events)

        # Check thresholds and alert
        for user_id, attempts in failures_by_user.items():
            if len(attempts) >= 5:  # Threshold for user-based alerts
                await self._alert_excessive_failures(
                    user_id=user_id,
                    ip_addresses=list({e.ip_address for e in attempts})
                )

        for ip, attempts in failures_by_ip.items():
            if len(attempts) >= 10:  # Threshold for IP-based alerts
                await self._alert_suspicious_ip(
                    ip_address=ip,
                    event_count=len(attempts)
                )

    async def analyze_security_trends(self, days: int = 7) -> Dict[str, Any]:
        """Analyze security trends over time period."""
        since = datetime.utcnow() - timedelta(days=days)
        events = await self.repository.get_security_events(start_date=since)

        return {
            "total_events": len(events),
            "events_by_type": self._count_events_by_type(events),
            "events_by_severity": self._count_events_by_severity(events),
            "top_ips": self._get_top_ips(events),
            "top_user_agents": self._get_top_user_agents(events)
        }

    async def _handle_suspicious_ip(
        self,
        ip_address: str,
        activity_data: Dict[str, Any]
    ) -> None:
        """Handle detection of suspicious IP activity."""
        # Log security event
        await self.repository.create_security_event({
            "event_type": SecurityEventType.SUSPICIOUS_ACTIVITY,
            "severity": "high",
            "description": f"Suspicious activity detected from IP: {ip_address}",
            "metadata": activity_data
        })

        # Send alert
        self.background_tasks.add_task(
            self.notification_service.send_security_alert,
            title="Suspicious IP Activity Detected",
            message=f"Multiple suspicious actions from IP: {ip_address}",
            details=activity_data
        )

    def _is_suspicious_activity(self, activity_data: Dict[str, Any]) -> bool:
        """Determine if activity pattern is suspicious."""
        failed_logins = activity_data.get("failed_logins", 0)
        access_denied = activity_data.get("access_denied", 0)

        # Define suspicious patterns
        return (
            failed_logins >= 5 or  # Multiple failed logins
            access_denied >= 3 or  # Multiple access denied
            (failed_logins + access_denied) >= 7  # Combined suspicious actions
        )

    @staticmethod
    def _count_events_by_type(events: List[Dict]) -> Dict[str, int]:
        """Count events by type."""
        counts = {}
        for event in events:
            event_type = event["event_type"]
            counts[event_type] = counts.get(event_type, 0) + 1
        return counts

    @staticmethod
    def _get_top_ips(events: List[Dict], limit: int = 10) -> List[Dict[str, Any]]:
        """Get top IPs by event count."""
        ip_counts = {}
        for event in events:
            ip = event["ip_address"]
            if ip:
                ip_counts[ip] = ip_counts.get(ip, 0) + 1

        return sorted(
            [{"ip": ip, "count": count} for ip, count in ip_counts.items()],
            key=lambda x: x["count"],
            reverse=True
        )[:limit]

    def _analyze_ip_activities(self, events: List[Dict]) -> Dict[str, Dict[str, Any]]:
        """Analyze events grouped by IP address."""
        ip_activities = {}

        for event in events:
            ip = event["ip_address"]
            if not ip:
                continue

            if ip not in ip_activities:
                ip_activities[ip] = {
                    "failed_logins": 0,
                    "access_denied": 0,
                    "suspicious_activity": 0,
                    "first_seen": event["timestamp"],
                    "last_seen": event["timestamp"],
                    "user_ids": set(),
                    "events": []
                }

            activity = ip_activities[ip]
            activity["last_seen"] = max(
                activity["last_seen"], event["timestamp"])

            if event["user_id"]:
                activity["user_ids"].add(event["user_id"])

            activity["events"].append(event)

            if event["event_type"] == SecurityEventType.LOGIN_FAILED:
                activity["failed_logins"] += 1
            elif event["event_type"] == SecurityEventType.ACCESS_DENIED:
                activity["access_denied"] += 1
            elif event["event_type"] == SecurityEventType.SUSPICIOUS_ACTIVITY:
                activity["suspicious_activity"] += 1

        return ip_activities

    def _group_failures_by_user(self, events: List[Dict]) -> Dict[int, List[Dict]]:
        """Group failed login attempts by user ID."""
        failures = {}
        for event in events:
            if event["user_id"]:
                if event["user_id"] not in failures:
                    failures[event["user_id"]] = []
                failures[event["user_id"]].append(event)
        return failures

    def _group_failures_by_ip(self, events: List[Dict]) -> Dict[str, List[Dict]]:
        """Group failed login attempts by IP address."""
        failures = {}
        for event in events:
            ip = event["ip_address"]
            if ip:
                if ip not in failures:
                    failures[ip] = []
                failures[ip].append(event)
        return failures

    async def _alert_excessive_failures(
        self,
        user_id: int,
        ip_addresses: List[str]
    ) -> None:
        """Alert on excessive login failures for a user."""
        await self.repository.create_security_event({
            "event_type": SecurityEventType.SUSPICIOUS_ACTIVITY,
            "severity": "high",
            "description": f"Excessive login failures for user ID: {user_id}",
            "metadata": {
                "user_id": user_id,
                "ip_addresses": ip_addresses
            }
        })

        self.background_tasks.add_task(
            self.notification_service.send_security_alert,
            title="Excessive Login Failures",
            message=f"Multiple failed login attempts detected for user ID: {
                user_id}",
            details={
                "user_id": user_id,
                "ip_addresses": ip_addresses
            }
        )

    async def _alert_suspicious_ip(
        self,
        ip_address: str,
        event_count: int
    ) -> None:
        """Alert on suspicious IP activity."""
        await self.repository.create_security_event({
            "event_type": SecurityEventType.SUSPICIOUS_ACTIVITY,
            "severity": "high",
            "description": f"High number of failed attempts from IP: {ip_address}",
            "metadata": {
                "ip_address": ip_address,
                "event_count": event_count
            }
        })

        self.background_tasks.add_task(
            self.notification_service.send_security_alert,
            title="Suspicious IP Activity",
            message=f"High number of failed attempts from IP: {ip_address}",
            details={
                "ip_address": ip_address,
                "event_count": event_count
            }
        )

    def _count_events_by_severity(self, events: List[Dict]) -> Dict[str, int]:
        """Count events by severity level."""
        counts = {}
        for event in events:
            severity = event.get("severity", "info")
            counts[severity] = counts.get(severity, 0) + 1
        return counts

    def _get_top_user_agents(self, events: List[Dict], limit: int = 10) -> List[Dict[str, Any]]:
        """Get top user agents by event count."""
        ua_counts = {}
        for event in events:
            ua = event.get("user_agent")
            if ua:
                ua_counts[ua] = ua_counts.get(ua, 0) + 1

        return sorted(
            [{"user_agent": ua, "count": count}
                for ua, count in ua_counts.items()],
            key=lambda x: x["count"],
            reverse=True
        )[:limit]
