from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Table, Text, JSON, Float, Index, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import Base

# Association tables
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
    Index('idx_user_roles_user_id', 'user_id'),
    Index('idx_user_roles_role_id', 'role_id'),
    extend_existing=True
)

role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id', ondelete='CASCADE'), primary_key=True),
    Index('idx_role_permissions_role_id', 'role_id'),
    Index('idx_role_permissions_permission_id', 'permission_id'),
    extend_existing=True
)

task_tags = Table(
    'task_tags',
    Base.metadata,
    Column('task_id', Integer, ForeignKey('tasks.id', ondelete='CASCADE'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True),
    Index('idx_task_tags_task_id', 'task_id'),
    Index('idx_task_tags_tag_id', 'tag_id'),
    extend_existing=True
)

class Role(Base):
    __tablename__ = "roles"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    users = relationship("User", secondary=user_roles, back_populates="roles")
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")

class Permission(Base):
    __tablename__ = "permissions"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(255))
    resource = Column(String(50), nullable=False)
    action = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")

class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        Index('idx_users_email', 'email'),
        Index('idx_users_created_at', 'created_at'),
        UniqueConstraint('email', name='uq_users_email'),
        UniqueConstraint('username', name='uq_users_username'),
        {'extend_existing': True}
    )
    
    id = Column(Integer, primary_key=True)
    email = Column(String(255), nullable=False, index=True)
    username = Column(String(50), nullable=False, index=True, unique=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_locked = Column(Boolean, default=False)
    locked_until = Column(DateTime, nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    # Relationships
    roles = relationship("Role", secondary=user_roles, back_populates="users")
    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    settings = relationship("UserSetting", back_populates="user", cascade="all, delete-orphan")
    auth_logs = relationship("AuthenticationLog", back_populates="user", cascade="all, delete-orphan")
    system_logs = relationship("SystemLog", back_populates="user", cascade="all, delete-orphan")
    search_queries = relationship("WebSearchQuery", back_populates="user", cascade="all, delete-orphan")
    files = relationship("File", back_populates="user", cascade="all, delete-orphan")
    health_metrics = relationship("HealthMetric", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    device_logs = relationship("DeviceControlLog", back_populates="user", cascade="all, delete-orphan")
    emotional_recognitions = relationship("EmotionalRecognition", back_populates="user", cascade="all, delete-orphan")
    model_usage_logs = relationship("ModelUsageLog", back_populates="user", cascade="all, delete-orphan")
    preferences = relationship("UserPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")
    comments = relationship("TaskComment", back_populates="user", cascade="all, delete-orphan")
    workflows = relationship("Workflow", back_populates="user", cascade="all, delete-orphan")
    password_resets = relationship("PasswordReset", back_populates="user", cascade="all, delete-orphan")

class Task(Base):
    __tablename__ = "tasks"
    __table_args__ = (
        Index('idx_tasks_user_id', 'user_id'),
        Index('idx_tasks_status_id', 'status_id'),
        Index('idx_tasks_due_date', 'due_date'),
        Index('idx_tasks_created_at', 'created_at'),
        CheckConstraint('due_date > created_at', name='ck_tasks_due_date_after_creation'),
        CheckConstraint('completion_date > created_at', name='ck_tasks_completion_after_creation'),
        {'extend_existing': True}
    )

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    status_id = Column(Integer, ForeignKey("task_status.id", ondelete='RESTRICT'), nullable=False)
    priority_id = Column(Integer, ForeignKey("task_priorities.id", ondelete='RESTRICT'), nullable=False)
    category_id = Column(Integer, ForeignKey("task_categories.id", ondelete='SET NULL'))
    due_date = Column(DateTime)
    start_date = Column(DateTime)
    completion_date = Column(DateTime)
    estimated_hours = Column(Float, CheckConstraint('estimated_hours >= 0'))
    actual_hours = Column(Float, CheckConstraint('actual_hours >= 0'))
    external_sync_id = Column(String(255), unique=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id", ondelete='CASCADE'), nullable=False)
    workflow_step_id = Column(Integer, ForeignKey("workflow_steps.id", ondelete='SET NULL'))

    # Relationships
    user = relationship("User", back_populates="tasks")
    status = relationship("TaskStatus", back_populates="tasks")
    priority = relationship("TaskPriority", back_populates="tasks")
    category = relationship("TaskCategory", back_populates="tasks")
    tags = relationship("Tag", secondary=task_tags, back_populates="tasks")
    attachments = relationship("TaskAttachment", back_populates="task", cascade="all, delete-orphan")
    comments = relationship("TaskComment", back_populates="task", cascade="all, delete-orphan")
    history = relationship("TaskHistory", back_populates="task", cascade="all, delete-orphan")
    summary = relationship("SummarizedContent", back_populates="task", uselist=False, cascade="all, delete-orphan")
    workflow_step = relationship("WorkflowStep", back_populates="tasks")

class TaskCategory(Base):
    __tablename__ = "task_categories"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(255))
    color_code = Column(String(7))
    icon = Column(String(50))
    parent_id = Column(Integer, ForeignKey("task_categories.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tasks = relationship("Task", back_populates="category")
    subcategories = relationship("TaskCategory")

class Tag(Base):
    __tablename__ = "tags"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    color_code = Column(String(7))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    tasks = relationship("Task", secondary=task_tags, back_populates="tags")

class TaskAttachment(Base):
    __tablename__ = "task_attachments"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(1000), nullable=False)
    file_type = Column(String(100))
    file_size = Column(Integer)  # in bytes
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    uploaded_by = Column(Integer, ForeignKey("users.id"))

    # Relationships
    task = relationship("Task", back_populates="attachments")

class TaskComment(Base):
    __tablename__ = "task_comments"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    content = Column(Text, nullable=False)
    parent_id = Column(Integer, ForeignKey("task_comments.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    task = relationship("Task", back_populates="comments")
    user = relationship("User", back_populates="comments")
    replies = relationship("TaskComment")

class TaskHistory(Base):
    __tablename__ = "task_history"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    change_type = Column(String(50))  # status, priority, assignment, etc.
    old_value = Column(JSON)
    new_value = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationships
    task = relationship("Task", back_populates="history")

class Workflow(Base):
    __tablename__ = "workflows"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    template_id = Column(Integer, ForeignKey("workflow_templates.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    template = relationship("WorkflowTemplate", back_populates="workflows")
    steps = relationship("WorkflowStep", back_populates="workflow")
    user = relationship("User", back_populates="workflows")

class WorkflowTemplate(Base):
    __tablename__ = "workflow_templates"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    category = Column(String(50))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    workflows = relationship("Workflow", back_populates="template")

class WorkflowStep(Base):
    __tablename__ = "workflow_steps"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"))
    name = Column(String(100), nullable=False)
    description = Column(Text)
    order = Column(Integer, nullable=False)
    step_type = Column(String(50))  # manual, automated, approval
    configuration = Column(JSON)
    status = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    workflow = relationship("Workflow", back_populates="steps")
    tasks = relationship("Task", back_populates="workflow_step")

class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String(255), nullable=False)
    content = Column(Text)
    type = Column(String(50))  # task, workflow, system, etc.
    priority = Column(String(20))
    read = Column(Boolean, default=False)
    read_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="notifications")

class TaskStatus(Base):
    __tablename__ = "task_status"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(255))
    color_code = Column(String(7))  # Hex color code
    
    # Relationships
    tasks = relationship("Task", back_populates="status")

class TaskPriority(Base):
    __tablename__ = "task_priorities"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(255))
    weight = Column(Integer)  # For sorting
    color_code = Column(String(7))  # Hex color code
    
    # Relationships
    tasks = relationship("Task", back_populates="priority")

class UserSession(Base):
    """User session model for tracking active user sessions."""
    
    __tablename__ = "user_sessions"
    __table_args__ = (
        Index('idx_user_sessions_user_id', 'user_id'),
        Index('idx_user_sessions_session_token', 'session_token'),
        Index('idx_user_sessions_expires_at', 'expires_at'),
        {'extend_existing': True}
    )
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete='CASCADE'), nullable=False)
    session_token = Column(String(255), unique=True, nullable=False)
    refresh_token = Column(String(255), unique=True, nullable=True)
    expires_at = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    device_info = Column(JSON)
    ip_address = Column(String(45))
    
    # Relationships
    user = relationship("User", back_populates="sessions")

class AuthenticationLog(Base):
    __tablename__ = "authentication_logs"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    timestamp = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String(45))
    user_agent = Column(String(255))
    login_status = Column(String(20))  # success, failed, locked
    failure_reason = Column(String(255), nullable=True)
    device_info = Column(JSON, nullable=True)

    # Relationships
    user = relationship("User", back_populates="auth_logs")

class SummarizedContent(Base):
    __tablename__ = "summarized_contents"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), unique=True)
    summary = Column(Text)
    keywords = Column(JSON)  # Array of keywords
    sentiment_score = Column(Integer)  # -1 to 1 scale
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    task = relationship("Task", back_populates="summary")

class SystemLog(Base):
    __tablename__ = "system_logs"
    __table_args__ = (
        Index('idx_system_logs_user_id', 'user_id'),
        Index('idx_system_logs_timestamp', 'timestamp'),
        {'extend_existing': True}
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete='SET NULL'))
    action = Column(String(100), nullable=False)
    details = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="system_logs")

class WebSearchQuery(Base):
    __tablename__ = "web_search_queries"
    __table_args__ = (
        Index('idx_web_search_queries_user_id', 'user_id'),
        Index('idx_web_search_queries_timestamp', 'timestamp'),
        {'extend_existing': True}
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete='CASCADE'))
    query = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    results = Column(JSON)
    
    # Relationships
    user = relationship("User", back_populates="search_queries")

class File(Base):
    __tablename__ = "files"
    __table_args__ = (
        Index('idx_files_user_id', 'user_id'),
        Index('idx_files_created_at', 'created_at'),
        {'extend_existing': True}
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete='CASCADE'))
    filename = Column(String(255), nullable=False)
    file_path = Column(String(1000), nullable=False)
    file_type = Column(String(50))
    file_size = Column(Integer, CheckConstraint('file_size >= 0'))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="files")

class HealthMetric(Base):
    __tablename__ = "health_metrics"
    __table_args__ = (
        Index('idx_health_metrics_user_id', 'user_id'),
        Index('idx_health_metrics_timestamp', 'timestamp'),
        {'extend_existing': True}
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete='CASCADE'))
    metric_type = Column(String(50), nullable=False)
    value = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="health_metrics")

class DeviceControlLog(Base):
    __tablename__ = "device_control_logs"
    __table_args__ = (
        Index('idx_device_control_logs_user_id', 'user_id'),
        Index('idx_device_control_logs_timestamp', 'timestamp'),
        {'extend_existing': True}
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete='CASCADE'))
    device_id = Column(String(100), nullable=False)
    action = Column(String(50), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50))
    
    # Relationships
    user = relationship("User", back_populates="device_logs")

class EmotionalRecognition(Base):
    __tablename__ = "emotional_recognitions"
    __table_args__ = (
        Index('idx_emotional_recognitions_user_id', 'user_id'),
        Index('idx_emotional_recognitions_timestamp', 'timestamp'),
        {'extend_existing': True}
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete='CASCADE'))
    emotion = Column(String(50), nullable=False)
    confidence = Column(Float, CheckConstraint('confidence >= 0 AND confidence <= 1'))
    timestamp = Column(DateTime, default=datetime.utcnow)
    source = Column(String(50))  # video, audio, text
    
    # Relationships
    user = relationship("User", back_populates="emotional_recognitions")

class ModelUsageLog(Base):
    __tablename__ = "model_usage_logs"
    __table_args__ = (
        Index('idx_model_usage_logs_user_id', 'user_id'),
        Index('idx_model_usage_logs_timestamp', 'timestamp'),
        {'extend_existing': True}
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete='CASCADE'))
    model_name = Column(String(100), nullable=False)
    operation = Column(String(50), nullable=False)
    input_data = Column(JSON)
    output_data = Column(JSON)
    execution_time = Column(Float, CheckConstraint('execution_time >= 0'))
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="model_usage_logs")

class UserSetting(Base):
    __tablename__ = "user_settings"
    __table_args__ = (
        UniqueConstraint('user_id', 'setting_key', name='uq_user_settings_user_key'),
        {'extend_existing': True}
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete='CASCADE'))
    setting_key = Column(String(100), nullable=False)
    setting_value = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="settings")

class UserPreference(Base):
    __tablename__ = "user_preferences"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    theme = Column(String(20), default="light")
    language = Column(String(10), default="en")
    notifications_enabled = Column(Boolean, default=True)
    accessibility_settings = Column(JSON)
    workflow_preferences = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="preferences")

class PasswordReset(Base):
    """Password reset tokens table."""
    __tablename__ = "password_resets"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="password_resets")
