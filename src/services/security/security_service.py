"""Security service module."""
from typing import Optional, Dict, Any
from datetime import datetime
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import SecurityContext
from src.core.security.events import SecurityEventType, SecurityEvent
from src.data.database.repositories.security_repository import SecurityRepository
from src.services.security.monitoring_service import SecurityMonitoringService
from src.services.notification_service.notification_service import NotificationService


class SecurityService:
    """Service for handling security operations."""

    def __init__(self, db: AsyncSession, context: SecurityContext):
        self.db = db
        self.context = context
        self.repository = SecurityRepository(db)
        self.monitoring_service = SecurityMonitoringService(
            db=db,
            notification_service=NotificationService()
        )

    async def log_security_event(
        self,
        event_type: SecurityEventType,
        description: str,
        severity: str = "info",
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log a security event."""
        event = SecurityEvent(
            event_type=event_type,
            timestamp=datetime.utcnow(),
            description=description,
            severity=severity,
            metadata=metadata or {},
            user_id=self.context.user_id,
            ip_address=self.context.client_ip,
            user_agent=self.context.user_agent
        )
        await self.repository.create_security_event(event)

    async def audit_request(
        self,
        request: Request,
        response_status: int,
        duration: float,
        error: Optional[str] = None
    ) -> None:
        """Audit an HTTP request."""
        await self.repository.create_audit_log({
            "event_type": "http_request",
            "user_id": self.context.user_id,
            "ip_address": self.context.client_ip,
            "user_agent": self.context.user_agent,
            "request_path": self.context.path,
            "request_method": self.context.method,
            "details": {
                "status_code": response_status,
                "duration": f"{duration:.3f}s",
                "error": error,
                "headers": dict(request.headers),
                "query_params": dict(request.query_params)
            }
        })

    async def check_suspicious_activity(self, request: Request) -> None:
        """Check for suspicious activity patterns."""
        is_suspicious = await self.monitoring_service.check_suspicious_activity(
            ip_address=self.context.client_ip,
            user_id=self.context.user_id
        )

        if is_suspicious:
            await self.log_security_event(
                event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
                description="Suspicious activity detected",
                severity="high",
                metadata={
                    "request_path": request.url.path,
                    "request_method": request.method,
                    "headers": dict(request.headers)
                }
            )
