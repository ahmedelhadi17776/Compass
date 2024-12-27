"""Security background tasks module."""
from typing import Optional
import asyncio
from datetime import datetime
import logging
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.services.security.monitoring_service import SecurityMonitoringService
from src.services.notification_service.notification_service import NotificationService
from src.data.database.session import get_db
from src.core.security.exceptions import SecurityConfigError

logger = logging.getLogger(__name__)


class SecurityBackgroundTasks:
    """Security background tasks handler."""

    def __init__(self, app: FastAPI):
        self.app = app
        self.is_running = False
        self.tasks = []

    async def start(self):
        """Start security background tasks."""
        self.is_running = True
        self.tasks = [
            asyncio.create_task(self._run_security_monitoring()),
            asyncio.create_task(self._run_security_cleanup())
        ]
        logger.info("Security background tasks started")

    async def stop(self):
        """Stop security background tasks."""
        self.is_running = False
        for task in self.tasks:
            task.cancel()
        await asyncio.gather(*self.tasks, return_exceptions=True)
        logger.info("Security background tasks stopped")

    async def _run_security_monitoring(self):
        """Run security monitoring tasks."""
        while self.is_running:
            try:
                async with AsyncSession() as db:
                    monitoring_service = SecurityMonitoringService(
                        db=db,
                        notification_service=NotificationService(),
                        background_tasks=self.app.background_tasks
                    )

                    # Check for suspicious activities
                    await monitoring_service.check_suspicious_activities(
                        timeframe_minutes=settings.SECURITY_MONITORING_INTERVAL
                    )

                    # Monitor authentication failures
                    await monitoring_service.monitor_authentication_failures()

                    # Analyze security trends
                    trends = await monitoring_service.analyze_security_trends(
                        days=1
                    )
                    logger.info(f"Security trends: {trends}")

            except Exception as e:
                logger.error(f"Error in security monitoring: {str(e)}")

            await asyncio.sleep(settings.SECURITY_MONITORING_INTERVAL * 60)

    async def _run_security_cleanup(self):
        """Run security-related cleanup tasks."""
        while self.is_running:
            try:
                async with AsyncSession() as db:
                    # Clean up old security events
                    await self._cleanup_old_events(db)

                    # Clean up expired sessions
                    await self._cleanup_expired_sessions(db)

            except Exception as e:
                logger.error(f"Error in security cleanup: {str(e)}")

            await asyncio.sleep(settings.SECURITY_CLEANUP_INTERVAL * 3600)

    async def _cleanup_old_events(self, db: AsyncSession):
        """Clean up old security events."""
        from src.data.database.repositories.security_repository import SecurityRepository

        repository = SecurityRepository(db)
        await repository.cleanup_old_events(
            days=settings.SECURITY_EVENT_RETENTION_DAYS
        )

    async def _cleanup_expired_sessions(self, db: AsyncSession):
        """Clean up expired sessions."""
        from src.data.database.repositories.session_repository import SessionRepository

        repository = SessionRepository(db)
        await repository.cleanup_expired_sessions()
