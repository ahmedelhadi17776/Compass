from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Index, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
from Backend.data_layer.database.models.base import Base
import datetime
import enum

class ProjectStatus(enum.Enum):
    ACTIVE = "Active"
    COMPLETED = "Completed"
    ARCHIVED = "Archived"
    ON_HOLD = "On Hold"

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(SQLAlchemyEnum(ProjectStatus), default=ProjectStatus.ACTIVE)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Foreign Key and Relationships
    organization_id = Column(Integer, ForeignKey(
        "organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    organization = relationship("Organization", back_populates="projects")
    tasks = relationship("Task", back_populates="project",
                         cascade="all, delete-orphan")
    members = relationship(
        "ProjectMember", back_populates="project", cascade="all, delete-orphan")
    creator = relationship("User", foreign_keys=[creator_id], backref="created_projects")

    __table_args__ = (
        Index("ix_project_name", "name"),
        Index("ix_project_organization_id", "organization_id"),
        Index("ix_project_created_at", "created_at"),
        Index("ix_project_status", "status"),
        Index("uq_project_org_name", "organization_id", "name", unique=True),
    )


class ProjectMember(Base):
    __tablename__ = "project_members"

    project_id = Column(Integer, ForeignKey(
        "projects.id", ondelete="CASCADE"), primary_key=True)
    user_id = Column(Integer, ForeignKey(
        "users.id", ondelete="CASCADE"), primary_key=True)
    role = Column(String(100))
    joined_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="members")
    user = relationship("User", back_populates="project_memberships")
