from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLAlchemyEnum, Index, JSON, ForeignKey, Text
from sqlalchemy.orm import relationship
from data_layer.database.models.base import Base
import datetime
import enum
from .task import Task


class WorkflowStatus(enum.Enum):
    ACTIVE = "Active"
    ARCHIVED = "Archived"


class Workflow(Base):
    __tablename__ = "workflows"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    status = Column(SQLAlchemyEnum(WorkflowStatus),
                    default=WorkflowStatus.ACTIVE, nullable=False)
    version = Column(String(50))
    settings = Column(JSON, nullable=True)
    triggers = Column(JSON, nullable=True)
    permissions = Column(JSON, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"))
    organization_id = Column(Integer, ForeignKey(
        "organizations.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow,
                        onupdate=datetime.datetime.utcnow)
    published_at = Column(DateTime)
    archived_at = Column(DateTime)

    # Relationships
    tasks = relationship("Task", back_populates="workflow",
                         cascade="all, delete-orphan")
    creator = relationship("User", foreign_keys=[created_by])
    organization = relationship("Organization", back_populates="workflows")
    steps = relationship(
        "WorkflowStep", back_populates="workflow", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_workflow_status", "status"),
        Index("ix_workflow_created_by", "created_by"),
        Index("ix_workflow_created_at", "created_at"),
        Index("ix_workflow_version", "version"),
        Index("ix_workflow_organization_id", "organization_id"),
    )
