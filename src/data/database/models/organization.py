from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from .base import Base
from sqlalchemy.sql import func


class Organization(Base):
    """Organization model for multi-tenant support."""
    __tablename__ = 'organizations'
    __table_args__ = (
        Index('ix_organizations_name', 'name', unique=True),
        {'extend_existing': True}
    )

    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey(
        "users.id", name='fk_organization_user_id'), unique=True)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    users = relationship("User", back_populates="organization")
    projects = relationship("Project", back_populates="organization")
