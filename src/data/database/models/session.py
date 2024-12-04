from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from ..base import Base

class UserSession(Base):
    """User session model for managing authentication sessions."""
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    session_token = Column(String, unique=True, index=True, nullable=False)
    refresh_token = Column(String, unique=True, nullable=True)
    is_active = Column(Boolean, default=True)
    device_info = Column(JSON, nullable=True)
    ip_address = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    ended_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="sessions")
