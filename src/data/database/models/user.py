"""User model and related functionality."""
from datetime import datetime
from enum import Enum
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, 
    ForeignKey, Index, JSON, Enum as SQLAEnum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base

class UserStatus(str, Enum):
    """User status enum."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"
    DELETED = "deleted"

class User(Base):
    """User model."""
    __tablename__ = "User"
    __table_args__ = (
        Index('ix_users_email', 'email', unique=True),
        Index('ix_users_username', 'username', unique=True),
        Index('ix_users_status', 'status'),
        {'extend_existing': True}
    )

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    status = Column(SQLAEnum(UserStatus), nullable=False, default=UserStatus.PENDING)
    
    # Profile
    first_name = Column(String(100))
    last_name = Column(String(100))
    avatar_url = Column(String(500))
    bio = Column(String(500))
    
    # Settings
    timezone = Column(String(50), default='UTC')
    locale = Column(String(10), default='en')
    notification_preferences = Column(JSON)
    
    # Security
    mfa_enabled = Column(Boolean, default=False)
    mfa_secret = Column(String(32))
    last_login = Column(DateTime(timezone=True))
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True))

    # Relationships
    roles = relationship("Role", secondary="user_roles", back_populates="users")
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    auth_logs = relationship("AuthLog", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    preferences = relationship("UserPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")
    tasks = relationship("Task", foreign_keys="[Task.user_id]", back_populates="user")
    created_tasks = relationship("Task", foreign_keys="[Task.creator_id]", back_populates="creator")
    feedback = relationship("Feedback", foreign_keys="[Feedback.user_id]", back_populates="user")
    device_controls = relationship("DeviceControl", back_populates="user")
    data_requests = relationship("DataRequest", back_populates="user")
    security_events = relationship("SecurityEvent", back_populates="user")
    web_searches = relationship("WebSearchQuery", back_populates="user")
    cache_entries = relationship("CacheEntry", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', status={self.status})>"