from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

class NotificationBase(BaseModel):
    """Base notification schema."""
    model_config = ConfigDict(from_attributes=True)
    
    title: str = Field(..., min_length=1, max_length=255)
    content: str
    notification_type: str = Field(..., min_length=1, max_length=50)
    priority: Optional[str] = Field(None, min_length=1, max_length=20)

class NotificationCreate(NotificationBase):
    """Notification creation schema."""
    model_config = ConfigDict(from_attributes=True)
    
    user_id: int

class NotificationUpdate(BaseModel):
    """Notification update schema."""
    model_config = ConfigDict(from_attributes=True)
    
    read: Optional[bool] = None
    archived: Optional[bool] = None

class NotificationResponse(NotificationBase):
    """Notification response schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    read: bool
    archived: bool
    created_at: datetime
    updated_at: datetime
