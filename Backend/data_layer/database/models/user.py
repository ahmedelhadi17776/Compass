"""User model and related functionality."""
from datetime import datetime
from enum import Enum
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime,
    ForeignKey, Index, JSON, Enum as SQLAEnum, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base
from .associations import user_roles


class UserStatus(str, Enum):
    """User status enum."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"
    DELETED = "deleted"


class User(Base):
    """User model."""
    __tablename__ = "users"
    __table_args__ = (
        Index('ix_users_email', 'email', unique=True),
        Index('ix_users_username', 'username', unique=True),
        Index('ix_users_status', 'status'),
        UniqueConstraint('email', name='uq_user_email'),
        {'extend_existing': True}
    )

    id = Column(Integer, primary_key=True)
    email = Column(String(255), nullable=False, unique=True)
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    status = Column(SQLAEnum(UserStatus), nullable=False,
                    default=UserStatus.PENDING)

    # Profile
    first_name = Column(String(100))
    last_name = Column(String(100))
    avatar_url = Column(String(255))
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
    roles = relationship(
        "Role", secondary=user_roles, back_populates="users")
    auth_logs = relationship(
        "AuthLog", back_populates="user", cascade="all, delete-orphan")
    preferences = relationship(
        "UserPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")
    tasks = relationship(
        "Task", foreign_keys="[Task.user_id]", back_populates="user")
    created_tasks = relationship(
        "Task", foreign_keys="[Task.creator_id]", back_populates="creator")
    feedback = relationship(
        "Feedback", foreign_keys="[Feedback.user_id]", back_populates="user")
    device_controls = relationship(
        "DeviceControl", back_populates="user", cascade="all, delete-orphan")
    data_requests = relationship(
        "DataRequest", back_populates="user")
    security_events = relationship(
        "SecurityEvent", back_populates="user", cascade="all, delete-orphan")
    web_searches = relationship(
        "WebSearchQuery", back_populates="user")
    cache_entries = relationship(
        "CacheEntry", back_populates="user", cascade="all, delete-orphan")
    api_keys = relationship(
        "APIKey", back_populates="user", cascade="all, delete-orphan")
    user_roles = relationship(
        "UserRole", back_populates="user", cascade="all, delete-orphan")
    password_resets = relationship(
        "PasswordReset", back_populates="user", cascade="all, delete-orphan")
    model_usage_logs = relationship(
        "ModelUsageLog", back_populates="user", cascade="all, delete-orphan")
    background_jobs = relationship(
        "BackgroundJob", back_populates="creator", cascade="all, delete-orphan")
    feedback = relationship(
        "Feedback", back_populates="user", cascade="all, delete-orphan")
    created_tags = relationship(
        "Tag", back_populates="creator", cascade="all, delete-orphan")
    notifications = relationship(
        "Notification", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship(
        "Session", back_populates="user", cascade="all, delete-orphan")
    subscriptions = relationship(
        "Subscription", back_populates="user", cascade="all, delete-orphan")
    security_logs = relationship(
        "SecurityAuditLog", back_populates="user", cascade="all, delete-orphan")
    file_logs = relationship(
        "FileLog", back_populates="user", cascade="all, delete-orphan")
    feedback_comments = relationship(
        "FeedbackComment", back_populates="user", cascade="all, delete-orphan")
    device_logs = relationship(
        "DeviceControlLog", back_populates="user", cascade="all, delete-orphan")
    resolved_feedbacks = relationship(
        "Feedback", back_populates="resolver", foreign_keys='Feedback.resolved_by')
    health_metrics = relationship(
        "HealthMetric", back_populates="user", cascade="all, delete-orphan")
    emotional_records = relationship(
        "EmotionalRecognition", back_populates="user", cascade="all, delete-orphan")
    organization = relationship(
        "Organization", back_populates="users")
    privacy_settings = relationship(
        "PrivacySettings", back_populates="user", uselist=False, cascade="all, delete-orphan")
    security_audit_logs = relationship(
        "SecurityAuditLog", back_populates="user", cascade="all, delete-orphan")
    summaries = relationship(
        "Summary", back_populates="user", cascade="all, delete-orphan")
    task_comments = relationship(
        "TaskComment", back_populates="user", cascade="all, delete-orphan")
    task_attachments = relationship(
        "TaskAttachment", back_populates="user", cascade="all, delete-orphan")
    task_history = relationship(
        "TaskHistory", back_populates="user", cascade="all, delete-orphan")
    todos = relationship("Todo", back_populates="user",
                         cascade="all, delete-orphan")
    daily_habits = relationship(
        "DailyHabit", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', status={self.status})>"
