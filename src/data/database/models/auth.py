"""Authentication related models."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship

from ..base import Base
from src.utils.datetime_utils import utc_now

class PasswordReset(Base):
    """Password reset model."""
    __tablename__ = "password_resets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token = Column(String, nullable=False, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    used = Column(Boolean, default=False)

    # Relationships
    user = relationship("User", back_populates="password_resets")

class UserSession(Base):
    """User session model."""
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    session_token = Column(String, nullable=False, unique=True, index=True)
    refresh_token = Column(String, unique=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    ended_at = Column(DateTime(timezone=True))
    device_info = Column(JSON)
    ip_address = Column(String(45))

    # Relationships
    user = relationship("User", back_populates="sessions")
