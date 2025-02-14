from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Index, Text, JSON
from sqlalchemy.orm import relationship
from data_layer.database.models.base import Base
import datetime


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow,
                        onupdate=datetime.datetime.utcnow)
    deleted_at = Column(DateTime)
    first_name = Column(String(100))
    last_name = Column(String(100))
    avatar_url = Column(String(255))
    bio = Column(Text)
    timezone = Column(String(50))
    locale = Column(String(50))
    notification_preferences = Column(JSON)
    mfa_enabled = Column(Boolean, default=False)
    mfa_secret = Column(String(255))
    last_login = Column(DateTime)

    # Consolidated relationships
    roles = relationship("UserRole", back_populates="user",
                         cascade="all, delete-orphan")
    preferences = relationship(
        "UserPreferences", back_populates="user", uselist=False, cascade="all, delete-orphan")
    sessions = relationship(
        "Session", back_populates="user", cascade="all, delete-orphan")
    created_tasks = relationship(
        "Task", foreign_keys="[Task.creator_id]", back_populates="creator")
    assigned_tasks = relationship(
        "Task", foreign_keys="[Task.assignee_id]", back_populates="assignee")
    project_memberships = relationship(
        "ProjectMember", back_populates="user", cascade="all, delete-orphan")
    calendar_events = relationship(
        "CalendarEvent", back_populates="user", cascade="all, delete-orphan")
    agent_actions = relationship("AgentAction", back_populates="user")
    agent_feedback = relationship("AgentFeedback", back_populates="user")
    context_snapshots = relationship("ContextSnapshot", back_populates="user")
    files = relationship("File", back_populates="user")

    __table_args__ = (
        Index("ix_user_email", "email"),
    )


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(String(255))

    # Relationships
    users = relationship("UserRole", back_populates="role",
                         cascade="all, delete-orphan")


class UserRole(Base):
    __tablename__ = "user_roles"

    user_id = Column(Integer, ForeignKey(
        "users.id", ondelete="CASCADE"), primary_key=True)
    role_id = Column(Integer, ForeignKey(
        "roles.id", ondelete="CASCADE"), primary_key=True)

    # Relationships
    user = relationship("User", back_populates="roles")
    role = relationship("Role", back_populates="users")
