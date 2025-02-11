"""Role-based access control models."""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base
from .associations import role_permissions, user_roles  # Import association tables


class Role(Base):
    """Role model."""
    __tablename__ = "roles"
    __table_args__ = (
        Index('ix_roles_name', 'name', unique=True),
        {'extend_existing': True}
    )

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    user_id = Column(Integer, ForeignKey(
        "users.id", name='fk_role_user_id'), unique=True)
    description = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    permissions = relationship(
        "Permission", secondary=role_permissions, back_populates="roles")
    users = relationship(
        "User", secondary=user_roles, back_populates="roles")


class Permission(Base):
    """Permission model."""
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    role_id = Column(Integer, ForeignKey(
        "roles.id", name='fk_premission_role_id'), unique=True)
    description = Column(String(255))
    resource = Column(String(50), nullable=False)
    action = Column(String(50), nullable=False)

    # Relationships
    roles = relationship("Role", secondary=role_permissions,
                         back_populates="permissions")
