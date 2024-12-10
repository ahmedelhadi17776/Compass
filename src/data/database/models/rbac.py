"""Role-based access control models."""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, 
    Index, Table, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .user import User
from .base import Base

# Association table for role-permission many-to-many relationship
role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.id', ondelete="CASCADE",name='fk_role_permission_role_id'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id', ondelete="CASCADE",name='fk_role_permission'), primary_key=True),
    Column('created_at', DateTime(timezone=True), server_default=func.now()),  # Ensure this line is included
    UniqueConstraint('role_id', 'permission_id', name='uq_role_permission'),
    Index('ix_role_permissions_role', 'role_id'),
    Index('ix_role_permissions_permission', 'permission_id'),
)  # Close the parentheses here

class Role(Base):
    """Role model."""
    __tablename__ = "roles"
    __table_args__ = (
        Index('ix_roles_name', 'name', unique=True),
        {'extend_existing': True}
    )

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    permissions = relationship("Permission", secondary=role_permissions)
    users = relationship("UserRole", back_populates="role")

class UserRole(Base):
    """User-Role association model."""
    __tablename__ = "user_roles"
    __table_args__ = (
        Index('ix_user_roles_user', 'user_id'),
        Index('ix_user_roles_role', 'role_id'),
        Index('ix_user_roles_composite', 'user_id', 'role_id', unique=True),
        {'extend_existing': True}
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('User.id', ondelete="CASCADE",name='fk_user_role_user_id'), nullable=False)
    role_id = Column(Integer, ForeignKey('roles.id', ondelete="CASCADE",name='fk_user_role_role_id'), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="user_roles")
    role = relationship("Role", back_populates="users")

class Permission(Base):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(String(255))
    resource = Column(String(50), nullable=False)
    action = Column(String(50), nullable=False)

    # Relationships
    roles = relationship("Role", secondary="role_permissions")