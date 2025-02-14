from data_layer.database.models.workflow import Workflow
from sqlalchemy import Column, Integer, String, Text, JSON, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from data_layer.database.models.base import Base
import datetime


class WorkflowExecution(Base):
    __tablename__ = "workflow_executions"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey(
        "workflows.id", ondelete="CASCADE"))
    status = Column(String(50))
    start_time = Column(DateTime, default=datetime.datetime.utcnow)
    end_time = Column(DateTime)
    error_log = Column(Text)
    performance_metrics = Column(JSON)

    # Relationships
    workflow = relationship("Workflow", back_populates="executions")


class WorkflowAgentLink(Base):
    __tablename__ = "workflow_agent_links"

    workflow_id = Column(Integer, ForeignKey(
        "workflows.id", ondelete="CASCADE"), primary_key=True)
    agent_type = Column(String(100), primary_key=True)
    config = Column(JSON)
    assigned_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    workflow = relationship("Workflow", back_populates="agent_links")


# Update Workflow class to include these relationships
Workflow.executions = relationship(
    "WorkflowExecution", back_populates="workflow", cascade="all, delete-orphan")
Workflow.agent_links = relationship(
    "WorkflowAgentLink", back_populates="workflow", cascade="all, delete-orphan")
