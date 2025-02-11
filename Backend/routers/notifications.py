from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from Backend.data.database.connection import get_db
from Backend.services.authentication.auth_service import get_current_user
from Backend.application.schemas.notification import NotificationCreate, NotificationResponse
from Backend.services.notification_service.notification_service import NotificationService
from Backend.data.repositories.notification_repository import NotificationRepository

router = APIRouter(
    prefix="/notifications",
    tags=["notifications"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=List[NotificationResponse])
async def get_notifications(
    status: Optional[str] = Query(None, description="Filter notifications by status (read/unread)"),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all notifications for the current user."""
    notification_repository = NotificationRepository(db)
    notification_service = NotificationService(notification_repository)
    return await notification_service.get_user_notifications(current_user.id, status)

@router.post("/", response_model=NotificationResponse)
async def create_notification(
    notification: NotificationCreate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new notification."""
    notification_repository = NotificationRepository(db)
    notification_service = NotificationService(notification_repository)
    notification.user_id = current_user.id
    return await notification_service.create_notification(notification)

@router.post("/{notification_id}/read", response_model=NotificationResponse)
async def mark_as_read(
    notification_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark a notification as read."""
    notification_repository = NotificationRepository(db)
    notification_service = NotificationService(notification_repository)
    return await notification_service.mark_as_read(notification_id, current_user.id)

@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification(
    notification_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a notification."""
    notification_repository = NotificationRepository(db)
    notification_service = NotificationService(notification_repository)
    await notification_service.delete_notification(notification_id, current_user.id)

@router.post("/system", response_model=NotificationResponse)
async def create_system_notification(
    title: str,
    message: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a system notification."""
    notification_repository = NotificationRepository(db)
    notification_service = NotificationService(notification_repository)
    return await notification_service.create_system_notification(current_user.id, title, message)

@router.delete("/cleanup", status_code=status.HTTP_204_NO_CONTENT)
async def cleanup_notifications(
    days: int = Query(30, description="Number of days to keep notifications"),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Clean up old notifications."""
    notification_repository = NotificationRepository(db)
    notification_service = NotificationService(notification_repository)
    await notification_service.cleanup_old_notifications(current_user.id, days)
