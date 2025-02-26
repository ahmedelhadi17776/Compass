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
    description = Column(Text)
    workflow_type = Column(SQLEnum(WorkflowType),
                           default=WorkflowType.SEQUENTIAL)
    created_by = Column(Integer, ForeignKey("users.id"))
    organization_id = Column(Integer, ForeignKey(
        "organizations.id"), nullable=False)
    status = Column(SQLEnum(WorkflowStatus), default=WorkflowStatus.PENDING)

    # Configuration & Metadata
    config = Column(JSON)  # Workflow configuration
    workflow_metadata = Column(JSON)  # Additional metadata
    version = Column(String(50))  # Workflow version
    tags = Column(JSON)  # Workflow tags for categorization

    # AI Integration
    ai_enabled = Column(Boolean, default=False)
    # Minimum confidence for AI decisions
    ai_confidence_threshold = Column(Float)
    ai_override_rules = Column(JSON)  # Rules for AI decision override
    ai_learning_data = Column(JSON)  # Historical learning data

    # Performance Metrics
    average_completion_time = Column(Float)  # Average workflow completion time
    success_rate = Column(Float)  # Workflow success rate
    optimization_score = Column(Float)  # AI-calculated optimization score
    bottleneck_analysis = Column(JSON)  # Identified workflow bottlenecks

    # Time Management
    estimated_duration = Column(Integer)  # Estimated minutes to complete
    actual_duration = Column(Integer)  # Actual minutes to complete
    schedule_constraints = Column(JSON)  # Timing constraints
    deadline = Column(DateTime)

    # Error Handling
    error_handling_config = Column(JSON)  # Error handling rules
    retry_policy = Column(JSON)  # Retry configuration
    fallback_steps = Column(JSON)  # Fallback procedures

    # Audit & Compliance
    compliance_rules = Column(JSON)  # Compliance requirements
    audit_trail = Column(JSON)  # Detailed audit information
    access_control = Column(JSON)  # Access control rules

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
