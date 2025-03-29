from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum as SQLAlchemyEnum, Text, Index, Float, JSON
from sqlalchemy.orm import relationship
from Backend.data_layer.database.models.base import Base
from typing import List
import datetime
import enum
import json
from sqlalchemy.sql import func

# Define TaskStatus using Python's enum


class TaskStatus(enum.Enum):
    TODO = "To Do"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"
    BLOCKED = "Blocked"
    UNDER_REVIEW = "Under Review"
    DEFERRED = "Deferred"


class TaskPriority(enum.Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    URGENT = "Urgent"


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    status = Column(SQLAlchemyEnum(TaskStatus),
                    default=TaskStatus.TODO, nullable=False)
    priority = Column(SQLAlchemyEnum(TaskPriority),
                      default=TaskPriority.MEDIUM)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow,
                        onupdate=datetime.datetime.utcnow)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assignee_id = Column(Integer, ForeignKey("users.id"))
    reviewer_id = Column(Integer, ForeignKey("users.id"))
    category_id = Column(Integer, ForeignKey("task_categories.id"))
    parent_task_id = Column(Integer, ForeignKey("tasks.id"))
    estimated_hours = Column(Float)
    actual_hours = Column(Float)
    confidence_score = Column(Float)
    completed_at = Column(DateTime)
    start_date = Column(
        DateTime, default=datetime.datetime.utcnow, nullable=False)
    duration = Column(Float, nullable=True)
    due_date = Column(DateTime, nullable=True)
    status_updated_at = Column(
        DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    organization_id = Column(Integer, ForeignKey(
        "organizations.id"), nullable=False)

    # Foreign Key and Relationships
    project_id = Column(Integer, ForeignKey(
        "projects.id", ondelete="CASCADE"), nullable=False, index=True)
    project = relationship("Project", back_populates="tasks")

    # Optional workflow relationship; tasks may belong to a workflow.
    workflow_id = Column(Integer, ForeignKey(
        "workflows.id", ondelete="SET NULL"), nullable=True, index=True)

    # Store task dependencies as a list of task IDs
    _dependencies_list = Column(JSON, default=list, nullable=False)

    # Updated relationships - consolidated
    creator = relationship("User", foreign_keys=[
                           creator_id], back_populates="created_tasks")
    assignee = relationship("User", foreign_keys=[
                            assignee_id], back_populates="assigned_tasks")
    reviewer = relationship("User", foreign_keys=[
                            reviewer_id], back_populates="reviewed_tasks")
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
    calendar_event = relationship(
        "CalendarEvent", back_populates="task", uselist=False)

    # Task Management
    current_workflow_step_id = Column(Integer, ForeignKey("workflow_steps.id"))
    current_workflow_step = relationship("WorkflowStep", foreign_keys=[
                                         current_workflow_step_id], back_populates="current_tasks")
    ai_suggestions = Column(JSON)
    complexity_score = Column(Float)
    time_spent = Column(Integer)
    time_estimates = Column(JSON)
    focus_sessions = Column(JSON)
    interruption_logs = Column(JSON)
    progress_metrics = Column(
        JSON, server_default=func.json('{}'), nullable=False)
    blockers = Column(JSON, server_default=func.json('[]'), nullable=False)
    health_score = Column(Float)
    risk_factors = Column(JSON)

    # Task Analytics
    parent_task = relationship(
        "Task", remote_side=[id], back_populates="subtasks")
    subtasks = relationship("Task", back_populates="parent_task")

    @property
    def dependencies(self) -> List[int]:
        """Get task dependencies."""
        try:
            deps_list = self._dependencies_list
            if isinstance(deps_list, str):
                return json.loads(deps_list)
            if hasattr(deps_list, 'type'):  # Check if it's a Column
                return []
            if deps_list is None:
                return []
            if isinstance(deps_list, (list, tuple, set)):
                return list(deps_list)
            return []
        except (json.JSONDecodeError, TypeError):
            return []

    @dependencies.setter
    def dependencies(self, value: List[int]):
        """Set task dependencies."""
        self._dependencies_list = json.dumps(
            value) if value is not None else '[]'
        self.task_dependencies = value

    # Add to existing relationships
    agent_interactions = relationship(
        "TaskAgentInteraction", back_populates="task", cascade="all, delete-orphan")
    __table_args__ = (
        Index("ix_task_status", "status"),
        Index("ix_task_creator_id", "creator_id"),
        Index("ix_task_assignee_id", "assignee_id"),
        Index("ix_task_project_id", "project_id"),
        Index("ix_task_start_date", "start_date"),
        Index("ix_task_due_date", "due_date"),
        Index("ix_task_status_updated_at", "status_updated_at"),
        Index("ix_task_created_at", "created_at"),
        Index("ix_task_category_id", "category_id"),
        Index("ix_task_priority", "priority"),
        Index("ix_task_organization_id", "organization_id"),
        Index("ix_task_workflow_id", "workflow_id"),
        Index("ix_task_health_score", "health_score"),
    )
