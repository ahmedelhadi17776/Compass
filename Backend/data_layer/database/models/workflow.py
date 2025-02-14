from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLAlchemyEnum, Index
from sqlalchemy.orm import relationship
from data_layer.database.base import Base
import datetime
import enum


class WorkflowStatus(enum.Enum):
    ACTIVE = "Active"
    ARCHIVED = "Archived"


class Workflow(Base):
    __tablename__ = "workflows"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    status = Column(SQLAlchemyEnum(WorkflowStatus),
                    default=WorkflowStatus.ACTIVE, nullable=False)
    # You may change this to a JSON type if needed.
    settings = Column(String(255))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    tasks = relationship("Task", back_populates="workflow",
                         cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_workflow_status", "status"),
    )
