from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum as SQLAlchemyEnum, Text, Index, Float
from sqlalchemy.orm import relationship
from Backend.data_layer.database.models.base import Base
import datetime
import enum

# Define TaskStatus using Python's enum


class TaskStatus(enum.Enum):
    TODO = "To Do"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    status = Column(SQLAlchemyEnum(TaskStatus),
                    default=TaskStatus.TODO, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow,
                        onupdate=datetime.datetime.utcnow)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assignee_id = Column(Integer, ForeignKey("users.id"))
    priority = Column(String(50))
    category_id = Column(Integer, ForeignKey("task_categories.id"))
    confidence_score = Column(Float)
    completed_at = Column(DateTime)
    due_date = Column(DateTime)
    organization_id = Column(Integer, ForeignKey(
        "organizations.id"), nullable=False)

    # Foreign Key and Relationships
    project_id = Column(Integer, ForeignKey(
        "projects.id", ondelete="CASCADE"), nullable=False, index=True)
    project = relationship("Project", back_populates="tasks")

    # Optional workflow relationship; tasks may belong to a workflow.
    workflow_id = Column(Integer, ForeignKey(
        "workflows.id", ondelete="SET NULL"), nullable=True, index=True)

    # Updated relationships - consolidated
    creator = relationship("User", foreign_keys=[
                           creator_id], back_populates="created_tasks")
    assignee = relationship("User", foreign_keys=[
                            assignee_id], back_populates="assigned_tasks")
    category = relationship("TaskCategory", back_populates="tasks")
    workflow = relationship("Workflow", back_populates="tasks")
    organization = relationship("Organization", back_populates="tasks")
    attachments = relationship(
        "TaskAttachment", back_populates="task", cascade="all, delete-orphan")
    comments = relationship(
        "TaskComment", back_populates="task", cascade="all, delete-orphan")
    history = relationship(
        "TaskHistory", back_populates="task", cascade="all, delete-orphan")
    linked_todos = relationship("Todo", back_populates="linked_task")

    __table_args__ = (
        Index("ix_task_status", "status"),
        Index("ix_task_creator_id", "creator_id"),
        Index("ix_task_assignee_id", "assignee_id"),
        Index("ix_task_project_id", "project_id"),
        Index("ix_task_due_date", "due_date"),
        Index("ix_task_created_at", "created_at"),
        Index("ix_task_category_id", "category_id"),
        Index("ix_task_priority", "priority"),
        Index("ix_task_organization_id", "organization_id"),
    )
