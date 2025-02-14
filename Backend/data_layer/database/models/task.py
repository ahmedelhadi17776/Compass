from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum as SQLAlchemyEnum, Text, Index
from sqlalchemy.orm import relationship
from data_layer.database.base import Base
import datetime
import enum

# Define TaskStatus using Python's enum


class TaskStatus(enum.Enum):
    TODO = "To Do"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    status = Column(SQLAlchemyEnum(TaskStatus),
                    default=TaskStatus.TODO, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow,
                        onupdate=datetime.datetime.utcnow)

    # Foreign Key and Relationships
    project_id = Column(Integer, ForeignKey(
        "projects.id", ondelete="CASCADE"), nullable=False, index=True)
    project = relationship("Project", back_populates="tasks")

    # Optional workflow relationship; tasks may belong to a workflow.
    workflow_id = Column(Integer, ForeignKey(
        "workflows.id", ondelete="SET NULL"), nullable=True, index=True)
    workflow = relationship("Workflow", back_populates="tasks")

    __table_args__ = (
        Index("ix_task_status", "status"),
    )
