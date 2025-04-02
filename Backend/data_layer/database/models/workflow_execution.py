from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Float, Index, Enum as SQLEnum
from sqlalchemy.orm import relationship
from Backend.data_layer.database.models.base import Base
from Backend.data_layer.database.models.workflow import WorkflowStatus
from Backend.data_layer.database.models.workflow_step import StepStatus
import datetime


class WorkflowStepExecution(Base):
    __tablename__ = "workflow_step_executions"

    id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(Integer, ForeignKey(
        "workflow_executions.id"), nullable=False)
    step_id = Column(Integer, ForeignKey("workflow_steps.id"), nullable=False)
    status = Column(SQLEnum(StepStatus), default=StepStatus.PENDING, nullable=False)
    execution_priority = Column(Integer, default=0, nullable=False)
    execution_metadata = Column(JSON, default=lambda: {}, nullable=False)
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow,
                        onupdate=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    result = Column(JSON, default=lambda: {}, nullable=False)
    error = Column(String, nullable=True)

    # Relationships
    execution = relationship("WorkflowExecution", back_populates="steps")
    step = relationship("WorkflowStep")
    __table_args__ = (
        Index("ix_workflow_step_executions_execution_id", "execution_id"),
        Index("ix_workflow_step_executions_step_id", "step_id"),
        Index("ix_workflow_step_executions_status", "status"), 
    )


class WorkflowExecution(Base):
    __tablename__ = "workflow_executions"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey(
        "workflows.id", ondelete="CASCADE"), nullable=False)
    status = Column(SQLEnum(StepStatus), default=StepStatus.PENDING, nullable=False)    
    execution_priority = Column(Integer, default=0, nullable=False)
    execution_metadata = Column(JSON, default=lambda: {}, nullable=False)
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow,
                        onupdate=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    result = Column(JSON, default=lambda: {}, nullable=False)
    error = Column(String, nullable=True)

    # Relationships
    workflow = relationship("Workflow", back_populates="executions")
    steps = relationship("WorkflowStepExecution",
                         back_populates="execution", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_workflow_executions_workflow_id", "workflow_id"),
        Index("ix_workflow_executions_status", "status"),
    )


class WorkflowAgentLink(Base):
    __tablename__ = "workflow_agent_links"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey(
        "workflows.id", ondelete="CASCADE"), nullable=False)
    agent_id = Column(Integer, ForeignKey("agent_actions.id"), nullable=False)
    interaction_type = Column(String(100), nullable=False)
    confidence_score = Column(Float, nullable=True)
    interaction_metadata = Column(JSON, nullable=True)
    created_at = Column(
        DateTime, default=datetime.datetime.utcnow, nullable=False)

    # Relationships
    workflow = relationship("Workflow", back_populates="agent_links")
    agent = relationship("AgentAction")

    __table_args__ = (
        Index("ix_workflow_agent_links_workflow_id", "workflow_id"),
        Index("ix_workflow_agent_links_agent_id", "agent_id"),
    )
