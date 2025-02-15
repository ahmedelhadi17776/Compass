from sqlalchemy import Column, Integer, String, Text, JSON, ForeignKey, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from Backend.data_layer.database.models.base import Base
import datetime
import enum


class WorkflowStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class Workflow(Base):
    __tablename__ = "workflows"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"))
    organization_id = Column(Integer, ForeignKey(
        "organizations.id"), nullable=False)
    status = Column(String(50), default=WorkflowStatus.PENDING.value)
    config = Column(JSON)
    workflow_metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow,
                        onupdate=datetime.datetime.utcnow)

    # Relationships
    organization = relationship("Organization", back_populates="workflows")
    creator = relationship("User", foreign_keys=[created_by])
    steps = relationship(
        "WorkflowStep", back_populates="workflow", cascade="all, delete-orphan")
    executions = relationship(
        "WorkflowExecution", back_populates="workflow", cascade="all, delete-orphan")
    agent_links = relationship(
        "WorkflowAgentLink", back_populates="workflow", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="workflow")
