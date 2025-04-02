from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, JSON, Index, Text, Enum as SQLEnum, Float
from sqlalchemy.orm import relationship
from Backend.data_layer.database.models.base import Base
import datetime
import enum


class StepStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    FAILED = "failed"


class StepType(str, enum.Enum):
    MANUAL = "manual"
    AUTOMATED = "automated"
    APPROVAL = "approval"
    NOTIFICATION = "notification"
    INTEGRATION = "integration"
    DECISION = "decision"
    AI_TASK = "ai_task"


class WorkflowStep(Base):
    __tablename__ = "workflow_steps"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey(
        "workflows.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    step_type = Column(SQLEnum(StepType), nullable=False)
    step_order = Column(Integer, nullable=False)
    status = Column(SQLEnum(StepStatus), default=StepStatus.PENDING, nullable=False)
    config = Column(JSON, nullable=True)
    conditions = Column(JSON, nullable=True)
    timeout = Column(Integer, nullable=True)
    retry_config = Column(JSON, nullable=True)
    is_required = Column(Boolean, default=True, nullable=False)
    auto_advance = Column(Boolean, default=False, nullable=False)
    can_revert = Column(Boolean, default=False, nullable=False)
    dependencies = Column(JSON, default=lambda: [], nullable=False) # List of step IDs this step depends on
    version = Column(String(50), default="1.0.0", nullable=False)
    previous_version_id = Column(Integer, nullable=True)
    average_execution_time = Column(Float, default=0.0, nullable=False)
    success_rate = Column(Float, default=0.0, nullable=False)
    last_execution_result = Column(JSON, nullable=True)
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    notification_config = Column(JSON, nullable=True)  # Who to notify and when
    created_at = Column(
        DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow,
                        onupdate=datetime.datetime.utcnow)
    
    # Relationships
    workflow = relationship("Workflow", back_populates="steps")
    transitions_from = relationship(
        "WorkflowTransition", foreign_keys="[WorkflowTransition.from_step_id]", back_populates="from_step")
    transitions_to = relationship(
        "WorkflowTransition", foreign_keys="[WorkflowTransition.to_step_id]", back_populates="to_step")
    current_tasks = relationship(
        "Task", back_populates="current_workflow_step")
    assignee = relationship("User", foreign_keys=[assigned_to])

    __table_args__ = (
        Index("ix_workflow_step_workflow_id", "workflow_id"),
        Index("ix_workflow_step_order", "workflow_id",
              "step_order", unique=True),
    )



