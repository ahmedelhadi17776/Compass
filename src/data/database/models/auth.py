"""Authentication related models."""
from enum import Enum
from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, 
    ForeignKey, Index, JSON, Enum as SQLAEnum
)
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func
from datetime import datetime



from .base import Base
from .user import User
from src.utils.datetime_utils import utc_now

class AuthEventType(str, Enum):
    """Authentication event types."""
    LOGIN = "login"
    LOGOUT = "logout"
    PASSWORD_RESET = "password_reset"
    TWO_FACTOR = "two_factor"
    ACCOUNT_LOCKOUT = "account_lockout"
    API_KEY = "api_key"

class AuthStatus(str, Enum):
    """Authentication status types."""
    SUCCESS = "success"
    FAILED = "failed"
    BLOCKED = "blocked"
    PENDING = "pending"

class AuthLog(Base):
    """Authentication logging model."""
    __tablename__ = "auth_logs"
    __table_args__ = (
        Index('ix_auth_logs_user_id', 'user_id'),
        Index('ix_auth_logs_event_type', 'event_type'),
        Index('ix_auth_logs_created_at', 'created_at'),
        {'extend_existing': True}
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("User.id", ondelete='SET NULL', name='fk_auth_log_user_id'))
    event_type = Column(SQLAEnum(AuthEventType), nullable=False)
    status = Column(SQLAEnum(AuthStatus), nullable=False)
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    device_info = Column(JSON)
    details = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="auth_logs")

class PasswordReset(Base):
    """Password reset token model."""
    __tablename__ = "password_resets"
    __table_args__ = (
        Index('ix_password_resets_token', 'token', unique=True),
        Index('ix_password_resets_user', 'user_id'),
        {'extend_existing': True}
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("User.id", ondelete='CASCADE', name='fk_pass_reset_user_id'), nullable=False)
    token = Column(String(255), unique=True, nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True))
    ip_address = Column(String(45))

    def validate_expires_at(self, key, value):
        if value <= utc_now():
            raise ValueError("Expiration date must be in the future.")
        return value
    
    # Relationships
    user = relationship("User", back_populates="password_resets")
