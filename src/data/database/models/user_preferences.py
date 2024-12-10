"""User preferences and settings models."""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, 
    Boolean, JSON, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base
from .user import User

class UserPreference(Base):
    """User preferences model for UI/UX and application settings."""
    __tablename__ = "user_preferences"
    __table_args__ = (
        Index('ix_user_preferences_user', 'user_id', unique=True),
        {'extend_existing': True}
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("User.id", ondelete='CASCADE',name='fk_user_pref_user_id'), nullable=False, unique=True)
    
    # UI/UX Preferences
    theme = Column(String(20), nullable=False, default="light")
    language = Column(String(10), nullable=False, default="en")
    timezone = Column(String(50), nullable=False, default="UTC")
    date_format = Column(String(20), default="YYYY-MM-DD")
    time_format = Column(String(20), default="HH:mm")
    
    # Notification Settings
    notifications_enabled = Column(Boolean, nullable=False, default=True)
    email_notifications = Column(Boolean, nullable=False, default=True)
    push_notifications = Column(Boolean, nullable=False, default=True)
    notification_preferences = Column(JSON)  # Detailed notification settings
    
    # Accessibility
    accessibility_settings = Column(JSON)  # Font size, contrast, etc.
    
    # Feature Preferences
    workflow_preferences = Column(JSON)  # Workflow-specific settings
    dashboard_layout = Column(JSON)  # Dashboard widget configuration
    shortcuts = Column(JSON)  # Custom keyboard shortcuts
    
    # Privacy Settings
    data_sharing = Column(Boolean, nullable=False, default=False)
    analytics_tracking = Column(Boolean, nullable=False, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="preferences")

    def __repr__(self):
        return f"<UserPreference(user_id={self.user_id}, theme={self.theme}, language={self.language})>"
