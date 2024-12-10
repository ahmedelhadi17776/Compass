from datetime import datetime
from enum import Enum
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, 
    Text, JSON, Boolean, Index, Enum as SQLAEnum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .user import User
from .base import Base

class NotificationType(str, Enum):
    """Notification type enum."""
    SYSTEM = "system"
    TASK = "task"
    WORKFLOW = "workflow"
    SECURITY = "security"
    UPDATE = "update"
    REMINDER = "reminder"

class NotificationPriority(str, Enum):
    """Notification priority enum."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class NotificationChannel(str, Enum):
    """Notification channel enum."""
    IN_APP = "in_app"
    EMAIL = "email"
    PUSH = "push"
    SMS = "sms"

class Notification(Base):
    """Notification model."""
    __tablename__ = "notifications"
    __table_args__ = (
        Index('ix_notifications_user', 'user_id'),
        Index('ix_notifications_type', 'notification_type'),
        Index('ix_notifications_created', 'created_at'),
        Index('ix_notifications_read', 'is_read'),
        {'extend_existing': True}
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("User.id", ondelete='CASCADE',name='fk_notification_user_id'), nullable=False)
    notification_type = Column(SQLAEnum(NotificationType), nullable=False)
    priority = Column(SQLAEnum(NotificationPriority), nullable=False, default=NotificationPriority.NORMAL)
    
    # Content
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    deep_link = Column(String(1000))  # App-specific navigation link
    
    # Delivery
    channels = Column(JSON)  # List of NotificationChannel values
    scheduled_at = Column(DateTime(timezone=True))
    sent_at = Column(DateTime(timezone=True))
    
    # Status
    is_read = Column(Boolean, default=False, nullable=False)
    is_archived = Column(Boolean, default=False, nullable=False)
    read_at = Column(DateTime(timezone=True))
    
    # Additional Data
    additional_data = Column(JSON)  # Additional context/data
    icon = Column(String(100))  # Icon identifier
    action_buttons = Column(JSON)  # Custom action buttons
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True))

    # Relationships
    user = relationship("User", back_populates="notifications")

    def __repr__(self):
        return f"<Notification(id={self.id}, type={self.notification_type}, user_id={self.user_id})>"
