"""Session and authentication token management models."""
from datetime import datetime
from enum import Enum
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, ForeignKey, 
    JSON, Index, Enum as SQLAEnum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .user import User
from .base import Base

class SessionType(str, Enum):
    """Session type enum."""
    WEB = "web"
    MOBILE = "mobile"
    API = "api"
    SYSTEM = "system"

class SessionStatus(str, Enum):
    """Session status enum."""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    LOGGED_OUT = "logged_out"

class Session(Base):
    """User session model."""
    __tablename__ = "sessions"
    __table_args__ = (
        Index('ix_sessions_user', 'user_id'),
        Index('ix_sessions_token', 'session_token', unique=True),
        Index('ix_sessions_refresh', 'refresh_token', unique=True),
        Index('ix_sessions_status', 'status'),
        {'extend_existing': True}
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('User.id', ondelete='CASCADE',name='fk_session_user_id'), nullable=False)
    session_token = Column(String(255), unique=True, nullable=False)
    refresh_token = Column(String(255), unique=True)
    session_type = Column(SQLAEnum(SessionType), nullable=False, default=SessionType.WEB)
    status = Column(SQLAEnum(SessionStatus), nullable=False, default=SessionStatus.ACTIVE)

    # Device Info
    device_id = Column(String(255))
    device_info = Column(JSON)
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    location_info = Column(JSON)

    # Security
    mfa_verified = Column(Boolean, default=False)
    last_activity = Column(DateTime(timezone=True))
    last_ip = Column(String(45))
    security_events = Column(JSON)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked_at = Column(DateTime(timezone=True))

    # Relationships
    user = relationship("User", back_populates="sessions")

    def __repr__(self):
        return f"<Session(id={self.id}, user_id={self.user_id}, type={self.session_type})>"
