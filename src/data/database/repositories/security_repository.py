"""Security repository module."""
from typing import Optional, List, Dict
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.data.database.models.security_log import SecurityAuditLog, SecurityEvent
from .base_repository import BaseRepository


class SecurityRepository(BaseRepository):
    """Repository for security-related database operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def create_audit_log(self, data: Dict) -> SecurityAuditLog:
        """Create a new audit log entry."""
        audit_log = SecurityAuditLog(**data)
        self.session.add(audit_log)
        await self.session.commit()
        return audit_log

    async def create_security_event(self, data: Dict) -> SecurityEvent:
        """Create a new security event."""
        event = SecurityEvent(**data)
        self.session.add(event)
        await self.session.commit()
        return event

    async def get_audit_logs(
        self,
        user_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        event_type: Optional[str] = None
    ) -> List[SecurityAuditLog]:
        """Get audit logs with optional filters."""
        query = select(SecurityAuditLog)

        if user_id:
            query = query.filter(SecurityAuditLog.user_id == user_id)
        if start_date:
            query = query.filter(SecurityAuditLog.timestamp >= start_date)
        if end_date:
            query = query.filter(SecurityAuditLog.timestamp <= end_date)
        if event_type:
            query = query.filter(SecurityAuditLog.event_type == event_type)

        result = await self.session.execute(query)
        return result.scalars().all()
