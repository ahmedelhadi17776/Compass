from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from Backend.data_layer.database.models.base import Base
import datetime


class WorkflowStepExecution(Base):
    __tablename__ = "workflow_step_executions"

    id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(Integer, ForeignKey(
        "workflow_executions.id"), nullable=False)
    step_id = Column(Integer, ForeignKey("workflow_steps.id"), nullable=False)
    status = Column(String(50), default="pending")
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime)
    result = Column(JSON)
    error = Column(String)

    # Relationships
    execution = relationship("WorkflowExecution", back_populates="steps")
    step = relationship("WorkflowStep")


class WorkflowExecution(Base):
    __tablename__ = "workflow_executions"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"), nullable=False)
    status = Column(String(50), default="pending")
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime)
    result = Column(JSON)
    error = Column(String)

    # Relationships
    workflow = relationship("Workflow", back_populates="executions")
    steps = relationship("WorkflowStepExecution",
                         back_populates="execution", cascade="all, delete-orphan")


class WorkflowAgentLink(Base):
    __tablename__ = "workflow_agent_links"

    workflow_id = Column(Integer, ForeignKey(
        "workflows.id", ondelete="CASCADE"), primary_key=True)
    agent_type = Column(String(100), primary_key=True)
    config = Column(JSON)
    assigned_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    workflow = relationship("Workflow", back_populates="agent_links")
