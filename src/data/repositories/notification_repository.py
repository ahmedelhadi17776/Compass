"""Notification repository module."""
from typing import List
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models.notification import Notification
from core.exceptions import NotificationNotFoundError

class NotificationRepository:
    """Notification repository class."""

    def __init__(self, session: AsyncSession):
        """Initialize notification repository."""
        self._session = session

    async def create_notification(self, notification_data: dict) -> Notification:
        """Create a new notification."""
        notification = Notification(
            user_id=notification_data["user_id"],
            title=notification_data["title"],
            message=notification_data["message"],
            type=notification_data.get("type", "info"),
            status=notification_data.get("status", "unread"),
            created_at=datetime.utcnow()
        )
        self._session.add(notification)
        await self._session.commit()
        await self._session.refresh(notification)
        return notification

    async def get_notification(self, notification_id: int, user_id: int) -> Notification:
        """Get a notification by ID."""
        notification = await self._session.execute(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.user_id == user_id
            )
        )
        notification = notification.scalar_one_or_none()
        if not notification:
            raise NotificationNotFoundError(
                f"Notification with id {notification_id} not found"
            )
        return notification

    async def get_user_notifications(self, user_id: int, status: str = None) -> List[Notification]:
        """Get all notifications for a user."""
        query = select(Notification).where(Notification.user_id == user_id)
        if status:
            query = query.where(Notification.status == status)
        query = query.order_by(Notification.created_at.desc())
        notifications = await self._session.execute(query)
        return notifications.scalars().all()

    async def mark_as_read(self, notification_id: int, user_id: int) -> Notification:
        """Mark a notification as read."""
        notification = await self.get_notification(notification_id, user_id)
        notification.status = "read"
        notification.read_at = datetime.utcnow()
        await self._session.commit()
        await self._session.refresh(notification)
        return notification

    async def delete_notification(self, notification_id: int, user_id: int) -> None:
        """Delete a notification."""
        notification = await self.get_notification(notification_id, user_id)
        await self._session.delete(notification)
        await self._session.commit()

    async def delete_old_notifications(self, user_id: int, days: int) -> None:
        """Delete notifications older than specified days."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        await self._session.execute(
            select(Notification).where(
                Notification.user_id == user_id,
                Notification.created_at < cutoff_date
            ).delete()
        )
        await self._session.commit()
