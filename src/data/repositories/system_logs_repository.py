"""System logs repository module."""
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models.system_logs import SystemLog
from core.exceptions import LogNotFoundError

class SystemLogsRepository:
    """System logs repository class."""

    def __init__(self, session: AsyncSession):
        """Initialize system logs repository."""
        self._session = session

    async def create_log(self, log_data: dict) -> SystemLog:
        """Create a new system log entry."""
        log = SystemLog(
            user_id=log_data.get("user_id"),
            event_type=log_data["event_type"],
            description=log_data["description"],
            severity=log_data.get("severity", "info"),
            metadata=log_data.get("metadata"),
            timestamp=datetime.utcnow()
        )
        self._session.add(log)
        await self._session.commit()
        await self._session.refresh(log)
        return log

    async def get_log(self, log_id: int) -> SystemLog:
        """Get a specific log entry."""
        log = await self._session.execute(
            select(SystemLog).where(SystemLog.id == log_id)
        )
        log = log.scalar_one_or_none()
        if not log:
            raise LogNotFoundError(f"Log with id {log_id} not found")
        return log

    async def get_user_logs(
        self,
        user_id: int,
        event_type: Optional[str] = None,
        severity: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[SystemLog]:
        """Get logs for a specific user with optional filters."""
        query = select(SystemLog).where(SystemLog.user_id == user_id)
        
        if event_type:
            query = query.where(SystemLog.event_type == event_type)
        if severity:
            query = query.where(SystemLog.severity == severity)
        if start_date:
            query = query.where(SystemLog.timestamp >= start_date)
        if end_date:
            query = query.where(SystemLog.timestamp <= end_date)
            
        query = query.order_by(desc(SystemLog.timestamp)).limit(limit)
        logs = await self._session.execute(query)
        return logs.scalars().all()

    async def get_system_logs(
        self,
        event_type: Optional[str] = None,
        severity: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[SystemLog]:
        """Get system-wide logs with optional filters."""
        query = select(SystemLog)
        
        if event_type:
            query = query.where(SystemLog.event_type == event_type)
        if severity:
            query = query.where(SystemLog.severity == severity)
        if start_date:
            query = query.where(SystemLog.timestamp >= start_date)
        if end_date:
            query = query.where(SystemLog.timestamp <= end_date)
            
        query = query.order_by(desc(SystemLog.timestamp)).limit(limit)
        logs = await self._session.execute(query)
        return logs.scalars().all()

    async def delete_old_logs(self, days: int = 30) -> None:
        """Delete logs older than specified days."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        await self._session.execute(
            select(SystemLog).where(SystemLog.timestamp < cutoff_date).delete()
        )
        await self._session.commit()

    async def create_error_log(
        self, error_message: str, user_id: Optional[int] = None, metadata: Optional[dict] = None
    ) -> SystemLog:
        """Create an error log entry."""
        return await self.create_log({
            "user_id": user_id,
            "event_type": "error",
            "description": error_message,
            "severity": "error",
            "metadata": metadata
        })

    async def create_security_log(
        self, event_description: str, user_id: Optional[int] = None, metadata: Optional[dict] = None
    ) -> SystemLog:
        """Create a security-related log entry."""
        return await self.create_log({
            "user_id": user_id,
            "event_type": "security",
            "description": event_description,
            "severity": "warning",
            "metadata": metadata
        })
