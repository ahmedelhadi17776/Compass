from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship

from ..base import Base
from src.utils.datetime_utils import utc_now

class User(Base):
    """User model for authentication and user management."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_locked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utc_now)
    last_login = Column(DateTime, nullable=True)

    # Relationships
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    user_roles = relationship("UserRole", back_populates="user", cascade="all, delete-orphan")
    roles = relationship("Role", secondary="user_roles", back_populates="users", overlaps="user_roles")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    password_resets = relationship("PasswordReset", back_populates="user", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")
    comments = relationship("TaskComment", back_populates="user", cascade="all, delete-orphan")
    task_history = relationship("TaskHistory", back_populates="user", cascade="all, delete-orphan")
    created_tags = relationship("Tag", back_populates="creator", cascade="all, delete-orphan")
    created_workflows = relationship("Workflow", back_populates="creator", cascade="all, delete-orphan")
