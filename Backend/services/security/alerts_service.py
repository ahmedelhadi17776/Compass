"""Security alerts service."""
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from Backend.core.security.events import SecurityEventType
from Backend.services.notification_service.notification_service import NotificationService
from Backend.data.database.repositories.security_repository import SecurityRepository

logger = logging.getLogger(__name__)


class SecurityAlertsService:
    """Service for managing security alerts."""

    def __init__(
        self,
        db: AsyncSession,
        notification_service: NotificationService
    ):
        self.db = db
        self.repository = SecurityRepository(db)
        self.notification_service = notification_service

    async def process_security_event(
        self,
        event_type: SecurityEventType,
        details: Dict[str, Any],
        severity: str = "info"
    ) -> None:
        """Process a security event and trigger alerts if needed."""
        # Log the event
        await self.repository.create_security_event({
            "event_type": event_type,
            "severity": severity,
            "description": details.get("description", ""),
            "metadata": details
        })

        # Check if event requires immediate alert
        if self._requires_immediate_alert(event_type, severity, details):
            await self._send_immediate_alert(event_type, details)

    async def _send_immediate_alert(
        self,
        event_type: SecurityEventType,
        details: Dict[str, Any]
    ) -> None:
        """Send an immediate security alert."""
        alert_config = self._get_alert_config(event_type)

        await self.notification_service.send_security_alert(
            title=alert_config["title"].format(**details),
            message=alert_config["message"].format(**details),
            severity=alert_config["severity"],
            recipients=self._get_alert_recipients(alert_config["severity"])
        )

    def _requires_immediate_alert(
        self,
        event_type: SecurityEventType,
        severity: str,
        details: Dict[str, Any]
    ) -> bool:
        """Determine if event requires immediate alert."""
        # High severity events always trigger alerts
        if severity == "high":
            return True

        # Specific event types that require alerts
        if event_type in {
            SecurityEventType.SUSPICIOUS_ACTIVITY,
            SecurityEventType.ACCESS_DENIED,
            SecurityEventType.TOKEN_REVOKED
        }:
            return True

        # Multiple failed attempts
        if (
            event_type == SecurityEventType.LOGIN_FAILED and
            details.get("attempt_count", 0) >= 5
        ):
            return True

        return False

    @staticmethod
    def _get_alert_config(event_type: SecurityEventType) -> Dict[str, Any]:
        """Get alert configuration for event type."""
        return {
            SecurityEventType.SUSPICIOUS_ACTIVITY: {
                "title": "Suspicious Activity Detected",
                "message": "Suspicious activity detected: {description}",
                "severity": "high"
            },
            SecurityEventType.LOGIN_FAILED: {
                "title": "Multiple Failed Login Attempts",
                "message": "Multiple failed login attempts detected for user {user_id}",
                "severity": "medium"
            },
            SecurityEventType.ACCESS_DENIED: {
                "title": "Access Denied Alert",
                "message": "Access denied: {description}",
                "severity": "medium"
            },
            # Add more event type configurations as needed
        }.get(event_type, {
            "title": "Security Event",
            "message": "{description}",
            "severity": "low"
        })

    @staticmethod
    def _get_alert_recipients(severity: str) -> List[str]:
        """Get alert recipients based on severity."""
        # This could be configured in settings or database
        return {
            "high": ["security-team@example.com", "admin@example.com"],
            "medium": ["security-team@example.com"],
            "low": ["monitoring@example.com"]
        }.get(severity, ["monitoring@example.com"])
