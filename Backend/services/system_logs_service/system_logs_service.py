"""System logs service module."""
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from Backend.data.repositories.system_logs_repository import SystemLogsRepository
from Backend.data.database.models.system_logs import SystemLog

class SystemLogsService:
    """System logs service class."""

    def __init__(self, session: AsyncSession):
        """Initialize system logs service."""
        self._repository = SystemLogsRepository(session)

    async def log_event(
        self,
        event_type: str,
        description: str,
        user_id: Optional[int] = None,
        severity: str = "info",
        metadata: Optional[Dict] = None
    ) -> SystemLog:
        """Log a system event."""
        # Validate severity
        valid_severities = ["info", "warning", "error", "critical"]
        if severity not in valid_severities:
            raise ValueError(f"Invalid severity. Must be one of: {valid_severities}")

        # Validate event type
        valid_event_types = [
            "info", "error", "security", "performance",
            "user_action", "system_action", "api_call"
        ]
        if event_type not in valid_event_types:
            raise ValueError(f"Invalid event type. Must be one of: {valid_event_types}")

        return await self._repository.create_log({
            "user_id": user_id,
            "event_type": event_type,
            "description": description,
            "severity": severity,
            "metadata": metadata
        })

    async def log_error(
        self,
        error_message: str,
        user_id: Optional[int] = None,
        metadata: Optional[Dict] = None
    ) -> SystemLog:
        """Log an error event."""
        return await self._repository.create_error_log(
            error_message,
            user_id,
            metadata
        )

    async def log_security_event(
        self,
        event_description: str,
        user_id: Optional[int] = None,
        metadata: Optional[Dict] = None
    ) -> SystemLog:
        """Log a security-related event."""
        return await self._repository.create_security_log(
            event_description,
            user_id,
            metadata
        )

    async def get_user_activity_logs(
        self,
        user_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        event_type: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 50
    ) -> List[SystemLog]:
        """Get user activity logs with optional filters."""
        return await self._repository.get_user_logs(
            user_id=user_id,
            event_type=event_type,
            status=severity,
            limit=limit
        )

    async def get_system_activity_logs(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        event_type: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 50
    ) -> List[SystemLog]:
        """Get system-wide activity logs with optional filters."""
        return await self._repository.get_system_logs(
            event_type=event_type,
            severity=severity,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )

    async def cleanup_old_logs(self, days: int = 30) -> None:
        """Clean up logs older than specified days."""
        if days < 1:
            raise ValueError("Days must be a positive integer")
        await self._repository.delete_old_logs(days)

    async def log_api_call(
        self,
        endpoint: str,
        method: str,
        user_id: Optional[int] = None,
        response_status: Optional[int] = None,
        duration_ms: Optional[float] = None
    ) -> SystemLog:
        """Log an API call."""
        metadata = {
            "endpoint": endpoint,
            "method": method,
            "response_status": response_status,
            "duration_ms": duration_ms
        }
        
        severity = "info"
        if response_status and response_status >= 400:
            severity = "error" if response_status >= 500 else "warning"

        return await self.log_event(
            event_type="api_call",
            description=f"{method} {endpoint}",
            user_id=user_id,
            severity=severity,
            metadata=metadata
        )

    async def log_performance_metric(
        self,
        metric_name: str,
        value: float,
        unit: str,
        component: str,
        metadata: Optional[Dict] = None
    ) -> SystemLog:
        """Log a performance metric."""
        if metadata is None:
            metadata = {}
        
        metadata.update({
            "metric_name": metric_name,
            "value": value,
            "unit": unit,
            "component": component
        })

        return await self.log_event(
            event_type="performance",
            description=f"{component} {metric_name}: {value}{unit}",
            severity="info",
            metadata=metadata
        )

    async def get_error_summary(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict:
        """Get a summary of error logs."""
        error_logs = await self._repository.get_system_logs(
            event_type="error",
            start_date=start_date,
            end_date=end_date
        )

        summary = {
            "total_errors": len(error_logs),
            "error_by_severity": {},
            "most_recent_errors": error_logs[:5] if error_logs else []
        }

        for log in error_logs:
            severity = log.severity
            summary["error_by_severity"][severity] = summary["error_by_severity"].get(severity, 0) + 1

        return summary
