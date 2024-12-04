"""Workflow-related models."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text, JSON, Index, Table
from sqlalchemy.orm import relationship

from ..base import Base
from src.utils.datetime_utils import utc_now

# Association tables
workflow_step_transitions = Table(
    'workflow_step_transitions',
    Base.metadata,
    Column('from_step_id', Integer, ForeignKey('workflow_steps.id', ondelete='CASCADE'), primary_key=True),
    Column('to_step_id', Integer, ForeignKey('workflow_steps.id', ondelete='CASCADE'), primary_key=True),
    Index('idx_step_transitions_from', 'from_step_id'),
    Index('idx_step_transitions_to', 'to_step_id'),
    extend_existing=True
)

class Workflow(Base):
    """Workflow model for managing task workflows."""
    __tablename__ = "workflows"
    __table_args__ = (
        Index('idx_workflows_created_by', 'created_by'),
        Index('idx_workflows_name', 'name'),
        {'extend_existing': True}
    )

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # Relationships
    steps = relationship("WorkflowStep", back_populates="workflow", cascade="all, delete-orphan")
    creator = relationship("User", back_populates="created_workflows")

class WorkflowStep(Base):
    """Workflow step model."""
    __tablename__ = "workflow_steps"
    __table_args__ = (
        Index('idx_workflow_steps_workflow_id', 'workflow_id'),
        {'extend_existing': True}
    )

    id = Column(Integer, primary_key=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id", ondelete='CASCADE'))
    name = Column(String(100), nullable=False)
    description = Column(Text)
    order = Column(Integer)
    requirements = Column(JSON)  # JSON field for step completion requirements
    auto_advance = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # Relationships
    workflow = relationship("Workflow", back_populates="steps")
    tasks = relationship("Task", back_populates="workflow_step")
    next_steps = relationship(
        "WorkflowStep",
        secondary=workflow_step_transitions,
        primaryjoin=id==workflow_step_transitions.c.from_step_id,
        secondaryjoin=id==workflow_step_transitions.c.to_step_id,
        backref="previous_steps"
    )
