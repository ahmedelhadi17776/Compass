from sqlalchemy.orm import Session
from sqlalchemy.future import select
from typing import List, Optional

from src.data.database.models import Notification
from src.application.schemas.notification import NotificationCreate

class NotificationManager:
    def __init__(self, db: Session):
        self.db = db

    async def create_notification(self, notification: NotificationCreate, user_id: int) -> Notification:
        """Create a new notification."""
        db_notification = Notification(
            user_id=user_id,
            title=notification.title,
            message=notification.message,
            type=notification.type
        )
        self.db.add(db_notification)
        await self.db.commit()
        await self.db.refresh(db_notification)
        return db_notification

    async def get_notification(self, notification_id: int, user_id: int) -> Optional[Notification]:
        """Get a specific notification by ID."""
        stmt = select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_notifications(self, user_id: int) -> List[Notification]:
        """Get all notifications for a specific user."""
        stmt = select(Notification).where(Notification.user_id == user_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def mark_as_read(self, notification_id: int, user_id: int) -> Optional[Notification]:
        """Mark a notification as read."""
        notification = await self.get_notification(notification_id, user_id)
        if not notification:
            return None

        notification.read = True
        await self.db.commit()
        await self.db.refresh(notification)
        return notification

    async def delete_notification(self, notification_id: int, user_id: int) -> bool:
        """Delete a notification."""
        notification = await self.get_notification(notification_id, user_id)
        if not notification:
            return False

        await self.db.delete(notification)
        await self.db.commit()
        return True
