"""Security service module."""
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request

from src.core.security import SecurityContext, SecurityEventService
from src.core.security.events import SecurityEventType
from src.data.database.repositories.security_repository import SecurityRepository
from src.core.security.logging import SecurityLogger
from src.core.security.exceptions import SecurityError, SecurityConfigError


class SecurityService:
    """Service for handling security operations."""

    def __init__(self, db: AsyncSession, context: SecurityContext):
        self.db = db
        self.context = context
        self.repository = SecurityRepository(db)
        self.event_service = SecurityEventService(db)

    async def log_security_event(
        self,
        event_type: SecurityEventType,
        description: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log a security event."""
        await self.event_service.log_event(
            event_type=event_type,
            user_id=self.context.user_id,
            ip_address=self.context.client_ip,
            user_agent=self.context.user_agent,
            details={
                "description": description,
                "path": self.context.path,
                "method": self.context.method,
                **(metadata or {})
            }
        )

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

    async def log_auth_event(
        self,
        event_type: str,
        user_id: Optional[int],
        success: bool,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log an authentication event."""
        event = SecurityEventType.LOGIN_SUCCESS if success else SecurityEventType.LOGIN_FAILED

        await self.log_security_event(
            event_type=event,
            description=f"Authentication {event_type}: {
                'success' if success else 'failed'}",
            metadata={
                "user_id": user_id,
                **(details or {})
            }
        )
