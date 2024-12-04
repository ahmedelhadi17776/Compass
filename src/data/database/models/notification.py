from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship

from ..base import Base
from src.utils.datetime_utils import utc_now

class Notification(Base):
    """Notification model for user notifications."""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String(50), nullable=False)  # e.g., 'info', 'warning', 'error'
    is_read = Column(Boolean, default=False)
    notification_metadata = Column(JSON, nullable=True)  # Additional data specific to notification type
    created_at = Column(DateTime(timezone=True), default=utc_now)
    read_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="notifications")
