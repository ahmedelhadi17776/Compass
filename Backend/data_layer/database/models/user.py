from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Index
from sqlalchemy.orm import relationship
from data_layer.database.base import Base
import datetime


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow,
                        onupdate=datetime.datetime.utcnow)
    deleted_at = Column(DateTime)

    # Relationships
    roles = relationship("UserRole", back_populates="user",
                         cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_user_email", "email"),
    )


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(String(255))

    # Relationships
    users = relationship("UserRole", back_populates="role",
                         cascade="all, delete-orphan")


class UserRole(Base):
    __tablename__ = "user_roles"

    user_id = Column(Integer, ForeignKey(
        "users.id", ondelete="CASCADE"), primary_key=True)
    role_id = Column(Integer, ForeignKey(
        "roles.id", ondelete="CASCADE"), primary_key=True)

    # Relationships
    user = relationship("User", back_populates="roles")
    role = relationship("Role", back_populates="users")
