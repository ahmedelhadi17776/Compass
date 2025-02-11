"""Notification service module."""
from typing import List
from datetime import datetime

from ...data.repositories.notification_repository import NotificationRepository
from ...data.database.models.notification import Notification
from ...application.schemas.notification import NotificationCreate

class NotificationService:
    """Notification service class."""

    def __init__(self, notification_repository: NotificationRepository):
        """Initialize notification service."""
        self._repository = notification_repository

    async def create_notification(self, notification_data: NotificationCreate) -> Notification:
        """Create a new notification."""
        notification_dict = notification_data.dict()
        return await self._repository.create_notification(notification_dict)

    async def get_notification(self, notification_id: int, user_id: int) -> Notification:
        """Get a notification by ID."""
        return await self._repository.get_notification(notification_id, user_id)

    async def get_user_notifications(self, user_id: int, status: str = None) -> List[Notification]:
        """Get all notifications for a user."""
        return await self._repository.get_user_notifications(user_id, status)

    async def mark_as_read(self, notification_id: int, user_id: int) -> Notification:
        """Mark a notification as read."""
        return await self._repository.mark_as_read(notification_id, user_id)

    async def delete_notification(self, notification_id: int, user_id: int) -> None:
        """Delete a notification."""
        await self._repository.delete_notification(notification_id, user_id)

    async def create_task_notification(self, user_id: int, task_title: str, due_date: datetime) -> Notification:
        """Create a notification for a task."""
        notification_data = NotificationCreate(
            user_id=user_id,
            title=f"Task Due Soon: {task_title}",
            message=f"Your task '{task_title}' is due on {due_date.strftime('%Y-%m-%d %H:%M')}",
            type="task_reminder"
        )
        return await self.create_notification(notification_data)

    async def create_system_notification(self, user_id: int, title: str, message: str) -> Notification:
        """Create a system notification."""
        notification_data = NotificationCreate(
            user_id=user_id,
            title=title,
            message=message,
            type="system"
        )
        return await self.create_notification(notification_data)

    async def cleanup_old_notifications(self, user_id: int, days: int = 30) -> None:
        """Clean up old notifications."""
        await self._repository.delete_old_notifications(user_id, days)
