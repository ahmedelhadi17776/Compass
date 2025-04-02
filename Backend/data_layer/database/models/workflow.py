from sqlalchemy import Column, Integer, String, Text, JSON, ForeignKey, DateTime, Enum as SQLEnum, Float, Index, Boolean
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
    UNDER_REVIEW = "under_review"
    OPTIMIZING = "optimizing"


class WorkflowType(str, enum.Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"
    AI_DRIVEN = "ai_driven"
    HYBRID = "hybrid"


class Workflow(Base):
    __tablename__ = "workflows"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    workflow_type = Column(SQLEnum(WorkflowType),
                           default=WorkflowType.SEQUENTIAL, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    organization_id = Column(Integer, ForeignKey(
        "organizations.id"), nullable=False)
    status = Column(SQLEnum(WorkflowStatus),
                    default=WorkflowStatus.PENDING, nullable=False)

    # Configuration & Metadata
    config = Column(JSON, nullable=True)  # Workflow configuration
    workflow_metadata = Column(JSON, nullable=True)  # Additional metadata
    version = Column(String(50), nullable=True)  # Workflow version
    tags = Column(JSON, nullable=True)  # Workflow tags for categorization

    # AI Integration
    ai_enabled = Column(Boolean, default=False, nullable=False)
    # Minimum confidence for AI decisions
    ai_confidence_threshold = Column(Float, default=0.8, nullable=False)
    # Rules for AI decision override
    ai_override_rules = Column(JSON, default=lambda: {}, nullable=False)
    # Historical learning data
    ai_learning_data = Column(JSON, default=lambda: {}, nullable=False)

    # Performance Metrics
    # Average workflow completion time
    average_completion_time = Column(Float, default=0.0, nullable=False)
    # Workflow success rate
    success_rate = Column(Float, default=0.0, nullable=False)
    # AI-calculated optimization score
    optimization_score = Column(Float, default=0.0, nullable=False)
    # Identified workflow bottlenecks
    bottleneck_analysis = Column(JSON, default=lambda: {}, nullable=False)

    # Time Management
    # Estimated minutes to complete
    estimated_duration = Column(Integer, nullable=True)
    # Actual minutes to complete
    actual_duration = Column(Integer, nullable=True)
    schedule_constraints = Column(JSON, nullable=True)  # Timing constraints
    deadline = Column(DateTime, nullable=True)

    # Error Handling
    error_handling_config = Column(JSON, nullable=True)  # Error handling rules
    retry_policy = Column(JSON, nullable=True)  # Retry configuration
    fallback_steps = Column(JSON, nullable=True)  # Fallback procedures

    # Audit & Compliance
    compliance_rules = Column(JSON, nullable=True)  # Compliance requirements
    audit_trail = Column(JSON, nullable=True)  # Detailed audit information
    access_control = Column(JSON, nullable=True)  # Access control rules

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow,
                        onupdate=datetime.datetime.utcnow)
    last_executed_at = Column(DateTime)
    next_scheduled_run = Column(DateTime)

    # Relationships
    organization = relationship("Organization", back_populates="workflows")
    creator = relationship("User", foreign_keys=[
                           created_by], back_populates="created_workflows")
    steps = relationship(
        "WorkflowStep", back_populates="workflow", cascade="all, delete-orphan")
    executions = relationship(
        "WorkflowExecution", back_populates="workflow", cascade="all, delete-orphan")
    agent_links = relationship(
        "WorkflowAgentLink", back_populates="workflow", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="workflow")
    # Add to existing relationships in Workflow class
    agent_interactions = relationship(
        "WorkflowAgentInteraction",
        back_populates="workflow",
        cascade="all, delete-orphan"
    )
    __table_args__ = (
        Index("ix_workflow_organization_id", "organization_id"),
        Index("ix_workflow_status", "status"),
        Index("ix_workflow_created_at", "created_at"),
        Index("ix_workflow_type", "workflow_type"),
        Index("ix_workflow_success_rate", "success_rate"),
        Index("ix_workflow_optimization_score", "optimization_score"),
    )
