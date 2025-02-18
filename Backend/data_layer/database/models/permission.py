from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Index, Enum as SQLAlchemyEnum, JSON
from sqlalchemy.orm import relationship
from Backend.data_layer.database.models.base import Base
import datetime
import enum


class ResourceType(enum.Enum):
    TASK = "task"
    PROJECT = "project"
    USER = "user"
    ROLE = "role"
    CALENDAR = "calendar"
    FILE = "file"
    SETTING = "setting"
    REPORT = "report"
    AI_MODEL = "ai_model"
    WORKFLOW = "workflow"


class ActionType(enum.Enum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"
    MANAGE = "manage"
    SHARE = "share"
    APPROVE = "approve"


class Permission(Base):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text)
    resource = Column(SQLAlchemyEnum(ResourceType), nullable=False)
    action = Column(SQLAlchemyEnum(ActionType), nullable=False)
    conditions = Column(JSON)  # Additional conditions for the permission
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow,
                        onupdate=datetime.datetime.utcnow)

    # Relationships
    roles = relationship(
        "RolePermission", back_populates="permission", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_permissions_resource_action",
              "resource", "action", unique=True),
    )


class RolePermission(Base):
    __tablename__ = "role_permissions"

    role_id = Column(Integer, ForeignKey(
        "roles.id", ondelete="CASCADE"), primary_key=True)
    permission_id = Column(Integer, ForeignKey(
        "permissions.id", ondelete="CASCADE"), primary_key=True)
    granted_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    assigned_at = Column(DateTime, default=datetime.datetime.utcnow)
    # Optional expiration for temporary permissions
    expires_at = Column(DateTime)
    restrictions = Column(JSON)  # Additional restrictions on the permission

    # Relationships
    role = relationship("Role", back_populates="permissions")
    permission = relationship("Permission", back_populates="roles")
    granter = relationship("User", foreign_keys=[granted_by])
