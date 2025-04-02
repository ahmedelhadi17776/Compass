from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, JSON, Index, Text
from sqlalchemy.orm import relationship
from Backend.data_layer.database.models.base import Base
import datetime


class WorkflowStep(Base):
    __tablename__ = "workflow_steps"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey(
        "workflows.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    step_type = Column(String(50), nullable=False)
    step_order = Column(Integer, nullable=False)
    config = Column(JSON, nullable=True)
    conditions = Column(JSON, nullable=True)
    timeout = Column(Integer, nullable=True)
    retry_config = Column(JSON, nullable=True)
    is_required = Column(Boolean, default=True, nullable=False)
    auto_advance = Column(Boolean, default=False, nullable=False)
    can_revert = Column(Boolean, default=False, nullable=False)
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

    __table_args__ = (
        Index("ix_workflow_step_workflow_id", "workflow_id"),
        Index("ix_workflow_step_order", "workflow_id",
              "step_order", unique=True),
    )
