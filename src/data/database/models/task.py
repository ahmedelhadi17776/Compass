"""Task-related models."""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text, JSON, Float, Index, CheckConstraint, Table
from sqlalchemy.orm import relationship

from ..base import Base
from src.utils.datetime_utils import utc_now

# Association tables
task_tags = Table(
    'task_tags',
    Base.metadata,
    Column('task_id', Integer, ForeignKey('tasks.id', ondelete='CASCADE'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True),
    Index('idx_task_tags_task_id', 'task_id'),
    Index('idx_task_tags_tag_id', 'tag_id'),
    extend_existing=True
)

class Task(Base):
    """Task model for managing user tasks."""
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
    due_date = Column(DateTime(timezone=True))
    start_date = Column(DateTime(timezone=True))
    completion_date = Column(DateTime(timezone=True))
    estimated_hours = Column(Float, CheckConstraint('estimated_hours >= 0'))
    actual_hours = Column(Float, CheckConstraint('actual_hours >= 0'))
    external_sync_id = Column(String(255), unique=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
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

class TaskStatus(Base):
    """Task status model."""
    __tablename__ = "task_status"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(255))
    color_code = Column(String(7))
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # Relationships
    tasks = relationship("Task", back_populates="status")

class TaskPriority(Base):
    """Task priority model."""
    __tablename__ = "task_priorities"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(255))
    weight = Column(Integer)
    color_code = Column(String(7))
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # Relationships
    tasks = relationship("Task", back_populates="priority")

class TaskCategory(Base):
    """Task category model."""
    __tablename__ = "task_categories"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(255))
    color_code = Column(String(7))
    icon = Column(String(50))
    parent_id = Column(Integer, ForeignKey("task_categories.id"))
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # Relationships
    tasks = relationship("Task", back_populates="category")
    subcategories = relationship("TaskCategory")

class TaskAttachment(Base):
    """Task attachment model."""
    __tablename__ = "task_attachments"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(1000), nullable=False)
    file_type = Column(String(128))
    file_size = Column(Integer)
    uploaded_by = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # Relationships
    task = relationship("Task", back_populates="attachments")
    user = relationship("User", foreign_keys=[uploaded_by])

class TaskComment(Base):
    """Task comment model."""
    __tablename__ = "task_comments"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    parent_id = Column(Integer, ForeignKey("task_comments.id"))
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # Relationships
    task = relationship("Task", back_populates="comments")
    user = relationship("User", back_populates="comments")
    replies = relationship("TaskComment")

class TaskHistory(Base):
    """Task history model for tracking changes."""
    __tablename__ = "task_history"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    change_type = Column(String(50), nullable=False)
    old_value = Column(JSON)
    new_value = Column(JSON)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    # Relationships
    task = relationship("Task", back_populates="history")
    user = relationship("User", back_populates="task_history")
