"""Security events service."""
from enum import Enum
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from src.data.database.models.security_log import SecurityAuditLog
from .logging import SecurityLogger

logger = logging.getLogger(__name__)


class SecurityEventType(Enum):
    """Security event types."""
    # Authentication events
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"

    # User management events
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"

    # Password events
    PASSWORD_CHANGE = "password_change"
    PASSWORD_RESET = "password_reset"

    # Token events
    TOKEN_REVOKED = "token_revoked"

    # Access events
    ACCESS_DENIED = "access_denied"

    # Task events
    TASK_CREATED = "task_created"
    TASK_UPDATED = "task_updated"
    TASK_DELETED = "task_deleted"

    # Security events
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    ERROR = "error"


@dataclass
class SecurityEvent:
    """Security event data."""
    event_type: SecurityEventType
    user_id: Optional[int]
    ip_address: str
    user_agent: Optional[str]
    details: Dict[str, Any]
    timestamp: datetime = datetime.utcnow()


class SecurityEventService:
    """Service for handling security events."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_event(self, event: SecurityEvent) -> None:
        """Log a security event."""
        try:
            # Create audit log entry
            log_entry = SecurityAuditLog(
                event_type=event.event_type.value,
                user_id=event.user_id,
                ip_address=event.ip_address,
                user_agent=event.user_agent,
                timestamp=event.timestamp,
                details=event.details
            )

            self.db.add(log_entry)
            await self.db.commit()

            # Log to security logger
            SecurityLogger.info(
                f"Security event: {event.event_type.value}",
                extra={
                    "event_type": event.event_type.value,
                    "user_id": event.user_id,
                    "ip_address": event.ip_address,
                    "details": event.details
                }
            )

        except Exception as e:
            logger.error(f"Failed to log security event: {str(e)}")
            raise

    async def handle_suspicious_activity(
        self,
        user_id: Optional[int],
        ip_address: str,
        reason: str,
        details: Dict[str, Any]
    ) -> None:
        """Handle suspicious activity detection."""
        event = SecurityEvent(
            event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=None,
            details={
                "reason": reason,
                **details
            }
        )
        await self.log_event(event)
