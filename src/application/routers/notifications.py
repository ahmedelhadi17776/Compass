from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from src.data.database.connection import get_db
from src.services.authentication.auth_service import get_current_user
from src.application.schemas.notification import NotificationCreate, NotificationResponse
from src.services.notification_service.notification_manager import NotificationManager

router = APIRouter(
    prefix="/notifications",
    tags=["notifications"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=List[NotificationResponse])
async def get_notifications(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all notifications for the current user."""
    notification_manager = NotificationManager(db)
    return await notification_manager.get_user_notifications(current_user.id)

@router.post("/{notification_id}/read", response_model=NotificationResponse)
async def mark_as_read(
    notification_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark a notification as read."""
    notification_manager = NotificationManager(db)
    notification = await notification_manager.mark_as_read(notification_id, current_user.id)
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    return notification

@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification(
    notification_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a notification."""
    notification_manager = NotificationManager(db)
    success = await notification_manager.delete_notification(notification_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    return None
