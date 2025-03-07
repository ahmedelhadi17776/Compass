from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Index, Text, JSON
from sqlalchemy.orm import relationship
from Backend.data_layer.database.models.base import Base
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
    phone_number = Column(String(20))
    avatar_url = Column(String(255))
    bio = Column(Text)
    timezone = Column(String(50))
    locale = Column(String(50))
    notification_preferences = Column(JSON)
    mfa_enabled = Column(Boolean, default=False)
    mfa_secret = Column(String(255))
    last_login = Column(DateTime)
    failed_login_attempts = Column(Integer, default=0)
    last_failed_login = Column(DateTime)
    account_locked_until = Column(DateTime)
    password_changed_at = Column(DateTime)
    force_password_change = Column(Boolean, default=False)
    # Encrypted security questions and answers
    security_questions = Column(JSON)
    allowed_ip_ranges = Column(JSON)  # List of allowed IP ranges
    max_sessions = Column(Integer, default=5)  # Maximum concurrent sessions
    organization_id = Column(Integer, ForeignKey(
        "organizations.id", ondelete="SET NULL"), nullable=True)

    # Consolidated relationships
    organization = relationship("Organization", back_populates="users")
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
    reviewed_tasks = relationship(
        "Task", foreign_keys="[Task.reviewer_id]", back_populates="reviewer")
    project_memberships = relationship(
        "ProjectMember", back_populates="user", cascade="all, delete-orphan")
    calendar_events = relationship(
        "CalendarEvent", back_populates="user", cascade="all, delete-orphan")
    agent_actions = relationship("AgentAction", back_populates="user")
    agent_feedback = relationship("AgentFeedback", back_populates="user")
    context_snapshots = relationship("ContextSnapshot", back_populates="user")
    files = relationship("File", back_populates="user")
    uploaded_attachments = relationship(
        "TaskAttachment", foreign_keys="[TaskAttachment.uploaded_by]", back_populates="uploader")
    subscriptions = relationship(
        "Subscription", back_populates="user", cascade="all, delete-orphan")

    # New relationships
    productivity_metrics = relationship(
        "ProductivityMetrics", back_populates="user", cascade="all, delete-orphan")
    emotional_data = relationship(
        "EmotionalIntelligence", back_populates="user", cascade="all, delete-orphan")
    rag_queries = relationship("RAGQuery", back_populates="user")
    email_organization = relationship(
        "EmailOrganization", back_populates="user", uselist=False)
    ai_interactions = relationship("AIAgentInteraction", back_populates="user")
    meeting_notes = relationship("MeetingNotes", back_populates="user")
    security_logs = relationship("SecurityAuditLog", back_populates="user")
    granted_permissions = relationship(
        "RolePermission", foreign_keys="[RolePermission.granted_by]", back_populates="granter")
    workspace_settings = relationship(
        "UserWorkspaceSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")
    daily_summaries = relationship(
        "DailySummary", back_populates="user", cascade="all, delete-orphan")
    todos = relationship("Todo", back_populates="user",
                         cascade="all, delete-orphan")
    daily_habits = relationship("DailyHabit", back_populates="user",
                                cascade="all, delete-orphan")
    created_workflows = relationship(
        "Workflow", foreign_keys="[Workflow.created_by]", back_populates="creator")

    __table_args__ = (
        Index("ix_user_email", "email"),
        Index("ix_user_username", "username"),
        Index("ix_user_created_at", "created_at"),
        Index("ix_user_last_login", "last_login"),
        Index("ix_user_account_locked_until", "account_locked_until"),
        Index("ix_user_organization_id", "organization_id"),
        Index("ix_user_phone_number", "phone_number"),
    )


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow,
                        onupdate=datetime.datetime.utcnow)

    # Relationships
    users = relationship("UserRole", back_populates="role",
                         cascade="all, delete-orphan")
    permissions = relationship("RolePermission", back_populates="role",
                               cascade="all, delete-orphan")


class UserRole(Base):
    __tablename__ = "user_roles"

    user_id = Column(Integer, ForeignKey(
        "users.id", ondelete="CASCADE"), primary_key=True)
    role_id = Column(Integer, ForeignKey(
        "roles.id", ondelete="CASCADE"), primary_key=True)
    assigned_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="roles")
    role = relationship("Role", back_populates="users")
