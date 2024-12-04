"""Role-based access control models."""
from sqlalchemy import Column, Integer, String, Table, ForeignKey
from sqlalchemy.orm import relationship

from ..base import Base

# Association table for role-permission many-to-many relationship
role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.id', ondelete="CASCADE"), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id', ondelete="CASCADE"), primary_key=True)
)

class UserRole(Base):
    """User-Role association model."""
    __tablename__ = "user_roles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    role_id = Column(Integer, ForeignKey('roles.id', ondelete="CASCADE"), nullable=False)

    # Relationships
    user = relationship("User", back_populates="user_roles", overlaps="roles")
    role = relationship("Role", back_populates="user_roles", overlaps="users")

class Role(Base):
    """Role model for RBAC."""
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(255))

    # Relationships
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")
    users = relationship(
        "User",
        secondary="user_roles",
        back_populates="roles",
        overlaps="user"
    )
    user_roles = relationship("UserRole", back_populates="role", overlaps="users")

class Permission(Base):
    """Permission model for RBAC."""
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(255))
    resource = Column(String(50))  # e.g., "tasks", "users"
    action = Column(String(50))    # e.g., "create", "read", "update", "delete"

    # Relationships
    roles = relationship(
        "Role",
        secondary=role_permissions,
        back_populates="permissions"
    )
