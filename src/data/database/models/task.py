"""Task models module."""
from datetime import timedelta
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, Text, 
    Boolean, Enum as SQLAEnum, UniqueConstraint, Index,
    PrimaryKeyConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base
from .task_enums import TaskStatus, TaskPriority
#from .associations import task_tags
from .user import User
from .cache import CacheEntry  # Import CacheEntry
from ....utils import datetime_utils
from .associations import task_tags  # Import the task_tags table


class TaskCategory(Base):
    """Task category model."""
    __tablename__ = "task_categories"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(255))
    color_code = Column(String(7))
    icon = Column(String(50))
    parent_id = Column(Integer, ForeignKey("task_categories.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Self-referential relationship
    parent = relationship("TaskCategory", remote_side=[id], back_populates="children")
    children = relationship("TaskCategory", back_populates="parent")
    tasks = relationship("Task", back_populates="category")

class Task(Base):
    """Task model."""
    __tablename__ = "tasks"
    __table_args__ = (
        UniqueConstraint('title', 'user_id', name='uq_task_title_user'),
        Index('ix_tasks_user', 'user_id'),
        Index('ix_tasks_status', 'status'),
        Index('ix_tasks_priority', 'priority'),
        Index('ix_tasks_due_date', 'due_date'),
        {'extend_existing': True}
    )

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    user_id = Column(Integer, ForeignKey("User.id", ondelete='CASCADE',name='fk_task_user_id'), nullable=False)
    assignee_id = Column(Integer, ForeignKey("User.id",name='fk_assigned_user_id'))
    status = Column(SQLAEnum(TaskStatus), nullable=False, default=TaskStatus.TODO.value)
    priority = Column(SQLAEnum(TaskPriority), nullable=False, default=TaskPriority.MEDIUM.value)
    category_id = Column(Integer, ForeignKey("task_categories.id", name='fk_task_cat_id'),nullable=False)
    workflow_id = Column(Integer, ForeignKey("workflows.id", name='fk_task_workflow_id'),nullable=False)
    due_date = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True))
    creator_id = Column(Integer, ForeignKey("User.id", ondelete='CASCADE',name='fk_task_creator_user_id'), nullable=False)

 

    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="tasks")
    assignee = relationship("User", foreign_keys=[assignee_id])
    creator = relationship("User", foreign_keys=[creator_id])
    category = relationship("TaskCategory", back_populates="tasks")
    workflow = relationship("Workflow", back_populates="tasks")
    comments = relationship("TaskComment", back_populates="task", cascade="all, delete-orphan")
    attachments = relationship("TaskAttachment", back_populates="task", cascade="all, delete-orphan")
    tags = relationship("Tag", secondary=task_tags, back_populates="tasks")
    history = relationship("TaskHistory", back_populates="task", cascade="all, delete-orphan")

    def cache_task_details(self, session):
        """Cache the details of the task."""
        cache_entry = CacheEntry(
            cache_key=f"task_{self.id}",
            cache_value=str(self.id),  # Assuming you have a method to convert task to dict
            expires_at=datetime_utils.utcnow() + timedelta(hours=1),  # Set expiration time
            user_id=self.user_id  # Link to the user
        )
        session.add(cache_entry)
        session.commit()

class TaskComment(Base):
    """Task comment model."""
    __tablename__ = "task_comments"

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("tasks.id",name='fk_task_comm_task_id'), nullable=False)
    user_id = Column(Integer, ForeignKey("User.id",name='fk_task_comm_user_id'), nullable=False)
    content = Column(Text, nullable=False)
    parent_id = Column(Integer, ForeignKey("task_comments.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    task = relationship("Task", back_populates="comments")
    user = relationship("User")
    parent = relationship("TaskComment", remote_side=[id], back_populates="replies")
    replies = relationship("TaskComment", back_populates="parent")

class TaskAttachment(Base):
    """Task attachment model."""
    __tablename__ = "task_attachments"

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("tasks.id",name='fk_task_attach_task_id'), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_type = Column(String(100))
    file_size = Column(Integer)  # Size in bytes
    uploaded_by = Column(Integer, ForeignKey("User.id",name='fk_task_attach_user_id'), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    task = relationship("Task", back_populates="attachments")
    user = relationship("User")

class TaskHistory(Base):
    """Task history model."""
    __tablename__ = "task_history"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE",name='fk_task_hist_task_id'), nullable=False)
    user_id = Column(Integer, ForeignKey("User.id", ondelete="CASCADE",name='fk_task_hist_user_id'), nullable=False)
    action = Column(String, nullable=False)
    field = Column(String)
    old_value = Column(String)
    new_value = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    task = relationship("Task", back_populates="history")
    user = relationship("User", back_populates="task_history")
