from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from .base import Base
from sqlalchemy.sql import func


class Project(Base):
    """Project model to group tasks."""
    __tablename__ = 'projects'
    __table_args__ = (
        Index('ix_projects_name', 'name', unique=True),
        Index('ix_projects_organization', 'organization_id'),
        {'extend_existing': True}
    )

    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey(
        'organizations.id'), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    organization = relationship("Organization", back_populates="projects")
    tasks = relationship("Task", back_populates="project")
