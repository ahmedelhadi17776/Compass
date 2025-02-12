from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Index
from sqlalchemy.orm import relationship
from data_layer.database.base import Base
import datetime


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    projects = relationship(
        "Project", back_populates="organization", cascade="all, delete-orphan")

    __table_args__ = (
        # Unique index on name (already unique, but adding an explicit index for clarity)
        Index("ix_organization_name", "name", unique=True),
    )


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Foreign Key and Relationships
    organization_id = Column(Integer, ForeignKey(
        "organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    organization = relationship("Organization", back_populates="projects")
    tasks = relationship("Task", back_populates="project",
                         cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_project_name", "name"),
    )
