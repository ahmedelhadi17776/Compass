"""Security repository module."""
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from Backend.core.security.events import SecurityEvent
from Backend.data.database.models.security_log import SecurityAuditLog


class SecurityRepository:
    """Repository for security-related operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_security_event(self, event: SecurityEvent) -> None:
        """Create a security event."""
        log_entry = SecurityAuditLog(
            event_type=event.event_type,
            timestamp=event.timestamp,
            description=event.description,
            severity=event.severity,
            user_id=event.user_id,
            ip_address=event.ip_address,
            user_agent=event.user_agent,
            metadata=event.metadata
        )
        self.db.add(log_entry)
        await self.db.commit()

    async def create_audit_log(self, data: dict) -> None:
        """Create an audit log entry."""
        log_entry = SecurityAuditLog(**data)
        self.db.add(log_entry)
        await self.db.commit()

    async def get_security_events(
        self,
        start_date: datetime,
        end_date: Optional[datetime] = None,
        event_types: Optional[List[str]] = None
    ) -> List[SecurityAuditLog]:
        """Get security events within date range."""
        query = select(SecurityAuditLog).where(
            SecurityAuditLog.timestamp >= start_date
        )

        if end_date:
            query = query.where(SecurityAuditLog.timestamp <= end_date)
        if event_types:
            query = query.where(SecurityAuditLog.event_type.in_(event_types))

        result = await self.db.execute(query)
        return result.scalars().all()

    async def cleanup_old_events(self, days: int) -> None:
        """Clean up events older than specified days."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        await self.db.execute(
            select(SecurityAuditLog).where(
                SecurityAuditLog.timestamp < cutoff_date
            ).delete()
        )
        await self.db.commit()
