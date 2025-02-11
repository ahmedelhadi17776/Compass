"""Test notification repository."""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from Backend.data.repositories.notification_repository import NotificationRepository
from Backend.data.database.models.notification import Notification
from core.exceptions import NotificationNotFoundError

@pytest.mark.asyncio
async def test_create_notification(test_db: AsyncSession):
    """Test creating a notification."""
    repository = NotificationRepository(test_db)
    notification_data = {
        "user_id": 1,
        "title": "Test Notification",
        "message": "Test Message",
        "type": "info"
    }

    notification = await repository.create_notification(notification_data)
    assert notification.title == notification_data["title"]
    assert notification.message == notification_data["message"]
    assert notification.user_id == notification_data["user_id"]

@pytest.mark.asyncio
async def test_get_notification(test_db: AsyncSession):
    """Test getting a notification."""
    repository = NotificationRepository(test_db)
    notification_data = {
        "user_id": 1,
        "title": "Test Notification",
        "message": "Test Message",
        "type": "info",
        "status": "unread"
    }
    notification = Notification(**notification_data)
    test_db.add(notification)
    await test_db.commit()
    await test_db.refresh(notification)

    retrieved_notification = await repository.get_notification(notification.id, notification_data["user_id"])
    assert retrieved_notification.title == notification_data["title"]
    assert retrieved_notification.message == notification_data["message"]

@pytest.mark.asyncio
async def test_get_notification_not_found(test_db: AsyncSession):
    """Test getting a non-existent notification."""
    repository = NotificationRepository(test_db)
    with pytest.raises(NotificationNotFoundError):
        await repository.get_notification(999, 1)

@pytest.mark.asyncio
async def test_get_user_notifications(test_db: AsyncSession):
    """Test getting all notifications for a user."""
    repository = NotificationRepository(test_db)
    user_id = 1
    notifications_data = [
        {"title": "Notification 1", "message": "Message 1", "user_id": user_id},
        {"title": "Notification 2", "message": "Message 2", "user_id": user_id},
        {"title": "Notification 3", "message": "Message 3", "user_id": 2}  # Different user
    ]
    
    for notification_data in notifications_data:
        test_db.add(Notification(**notification_data))
    await test_db.commit()

    user_notifications = await repository.get_user_notifications(user_id)
    assert len(user_notifications) == 2
    assert all(notification.user_id == user_id for notification in user_notifications)

@pytest.mark.asyncio
async def test_mark_as_read(test_db: AsyncSession):
    """Test marking a notification as read."""
    repository = NotificationRepository(test_db)
    notification = Notification(
        title="Test Notification",
        message="Test Message",
        user_id=1,
        status="unread"
    )
    test_db.add(notification)
    await test_db.commit()
    await test_db.refresh(notification)

    updated_notification = await repository.mark_as_read(notification.id, 1)
    assert updated_notification.status == "read"
    assert updated_notification.read_at is not None

@pytest.mark.asyncio
async def test_delete_notification(test_db: AsyncSession):
    """Test deleting a notification."""
    repository = NotificationRepository(test_db)
    notification = Notification(
        title="Test Notification",
        message="Test Message",
        user_id=1
    )
    test_db.add(notification)
    await test_db.commit()
    await test_db.refresh(notification)

    await repository.delete_notification(notification.id, 1)
    with pytest.raises(NotificationNotFoundError):
        await repository.get_notification(notification.id, 1)

@pytest.mark.asyncio
async def test_delete_old_notifications(test_db: AsyncSession):
    """Test deleting old notifications."""
    repository = NotificationRepository(test_db)
    user_id = 1
    now = datetime.utcnow()
    
    # Create notifications with different dates
    notifications_data = [
        {
            "title": "Old Notification",
            "message": "Old Message",
            "user_id": user_id,
            "created_at": now - timedelta(days=31)
        },
        {
            "title": "Recent Notification",
            "message": "Recent Message",
            "user_id": user_id,
            "created_at": now - timedelta(days=15)
        }
    ]
    
    for notification_data in notifications_data:
        test_db.add(Notification(**notification_data))
    await test_db.commit()

    # Delete notifications older than 30 days
    await repository.delete_old_notifications(user_id, 30)
    
    remaining_notifications = await repository.get_user_notifications(user_id)
    assert len(remaining_notifications) == 1
    assert remaining_notifications[0].title == "Recent Notification"
