"""Privacy settings model module."""
from datetime import datetime
from sqlalchemy import Column, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from .user import User
from .base import Base


class PrivacySettings(Base):
    """Privacy settings model."""

    __tablename__ = "privacy_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey(
        "users.id", name='fk_privacy_sett_user_id'), unique=True)
    data_collection = Column(Boolean, default=True)
    data_sharing = Column(Boolean, default=False)
    marketing_communications = Column(Boolean, default=False)
    analytics_tracking = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="privacy_settings")
