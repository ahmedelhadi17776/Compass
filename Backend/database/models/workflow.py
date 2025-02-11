"""Workflow and process management models."""
from datetime import datetime
from enum import Enum
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey,
    Text, Boolean, JSON, Index, Enum as SQLAEnum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .user import User
from .base import Base


class WorkflowStatus(str, Enum):
    """Workflow status enum."""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"
    DEPRECATED = "deprecated"


class WorkflowStepType(str, Enum):
    """Workflow step type enum."""
    TASK = "task"
    APPROVAL = "approval"
    NOTIFICATION = "notification"
    AUTOMATION = "automation"
    CONDITION = "condition"
    INTEGRATION = "integration"


class Workflow(Base):
    """Workflow model for process management."""
    __tablename__ = "workflows"
    __table_args__ = (
        Index('ix_workflows_creator', 'created_by'),
        Index('ix_workflows_status', 'status'),
        Index('ix_workflows_category', 'category'),
        {'extend_existing': True}
    )

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(100))
    status = Column(SQLAEnum(WorkflowStatus), nullable=False,
                    default=WorkflowStatus.DRAFT)

    # Configuration
    version = Column(String(50), nullable=False, default="1.0.0")
    settings = Column(JSON)  # Workflow-specific settings
    triggers = Column(JSON)  # Events that start the workflow
    permissions = Column(JSON)  # Access control settings

    # Metadata
    tags = Column(JSON)
    created_by = Column(Integer, ForeignKey(
        "users.id", name='fk_workflow_created_by_user_id'), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    published_at = Column(DateTime(timezone=True))
    archived_at = Column(DateTime(timezone=True))

    # Relationships
    creator = relationship("User", back_populates="created_workflows")
    steps = relationship(
        "WorkflowStep", back_populates="workflow", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="workflow")


class WorkflowStep(Base):
    """Workflow step model."""
    __tablename__ = "workflow_steps"
    __table_args__ = (
        Index('ix_workflow_steps_workflow', 'workflow_id'),
        Index('ix_workflow_steps_type', 'step_type'),
        {'extend_existing': True}
    )

    id = Column(Integer, primary_key=True)
    workflow_id = Column(Integer, ForeignKey(
        "workflows.id", ondelete='CASCADE', name='fk_workflow_step_workflow_id'), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    step_type = Column(SQLAEnum(WorkflowStepType), nullable=False)
    order = Column(Integer, nullable=False)

    # Configuration
    config = Column(JSON, nullable=False)  # Step-specific configuration
    conditions = Column(JSON)  # Conditions for step execution
    timeout = Column(Integer)  # Timeout in seconds
    retry_config = Column(JSON)  # Retry settings

    # Behavior
    is_required = Column(Boolean, default=True, nullable=False)
    auto_advance = Column(Boolean, default=False, nullable=False)
    can_revert = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    workflow = relationship("Workflow", back_populates="steps")
    tasks = relationship("Task", back_populates="workflow_step")
    transitions_from = relationship(
        "WorkflowTransition",
        foreign_keys="[WorkflowTransition.from_step_id]",
        back_populates="from_step",
        cascade="all, delete-orphan"
    )
    transitions_to = relationship(
        "WorkflowTransition",
        foreign_keys="[WorkflowTransition.to_step_id]",
        back_populates="to_step",
        cascade="all, delete-orphan"
    )


class WorkflowTransition(Base):
    """Workflow transition model."""
    __tablename__ = "workflow_transitions"
    __table_args__ = (
        Index('ix_workflow_transitions_from', 'from_step_id'),
        Index('ix_workflow_transitions_to', 'to_step_id'),
        {'extend_existing': True}
    )

    id = Column(Integer, primary_key=True)
    from_step_id = Column(Integer, ForeignKey("workflow_steps.id", ondelete='CASCADE',
                          name='fk_workflow_trans_workflow_steps_id'), nullable=False)
    to_step_id = Column(Integer, ForeignKey("workflow_steps.id", ondelete='CASCADE',
                        name='fk_workflow_trans_to_workflow_id'), nullable=False)
    conditions = Column(JSON)  # Transition conditions
    triggers = Column(JSON)  # Events that trigger the transition
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    from_step = relationship("WorkflowStep", foreign_keys=[
                             from_step_id], back_populates="transitions_from")
    to_step = relationship("WorkflowStep", foreign_keys=[
                           to_step_id], back_populates="transitions_to")
