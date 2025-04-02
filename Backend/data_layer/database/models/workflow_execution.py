from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Float, Index
from sqlalchemy.orm import relationship
from Backend.data_layer.database.models.base import Base
import datetime


class WorkflowStepExecution(Base):
    __tablename__ = "workflow_step_executions"

    id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(Integer, ForeignKey(
        "workflow_executions.id"), nullable=False)
    step_id = Column(Integer, ForeignKey("workflow_steps.id"), nullable=False)
    status = Column(String(50), default="pending", nullable=False)
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    result = Column(JSON, nullable=True)
    error = Column(String, nullable=True)

    # Relationships
    execution = relationship("WorkflowExecution", back_populates="steps")
    step = relationship("WorkflowStep")


class WorkflowExecution(Base):
    __tablename__ = "workflow_executions"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"), nullable=False)
    status = Column(String(50), default="pending", nullable=False)
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    result = Column(JSON, nullable=True)
    error = Column(String, nullable=True)

    # Relationships
    workflow = relationship("Workflow", back_populates="executions")
    steps = relationship("WorkflowStepExecution",
                         back_populates="execution", cascade="all, delete-orphan")


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
