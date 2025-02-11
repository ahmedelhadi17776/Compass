"""Association tables for many-to-many relationships."""
from sqlalchemy import Column, Integer, ForeignKey, Table, Index, DateTime, UniqueConstraint
from sqlalchemy.sql import func

from .base import Base

# Association table for Role-Permission many-to-many relationship
role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column(
        'role_id',
        Integer,
        ForeignKey('roles.id', ondelete="CASCADE",
                   name='fk_role_permission_role_id'),
        primary_key=True
    ),
    Column(
        'permission_id',
        Integer,
        ForeignKey('permissions.id', ondelete="CASCADE",
                   name='fk_role_permission_permission_id'),
        primary_key=True
    ),
    Column('created_at', DateTime(timezone=True), server_default=func.now()),
    UniqueConstraint('role_id', 'permission_id', name='uq_role_permission'),
    Index('ix_role_permissions_role', 'role_id'),
    Index('ix_role_permissions_permission', 'permission_id'),
    extend_existing=True
)

# Association table for User-Role many-to-many relationship
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column(
        'user_id',
        Integer,
        ForeignKey('users.id', ondelete="CASCADE",
                   name='fk_user_role_user_id'),
        primary_key=True
    ),
    Column(
        'role_id',
        Integer,
        ForeignKey('roles.id', ondelete="CASCADE",
                   name='fk_user_role_role_id'),
        primary_key=True
    ),
    Column('created_at', DateTime(timezone=True), server_default=func.now()),
    UniqueConstraint('user_id', 'role_id', name='uq_user_role'),
    Index('ix_user_roles_user', 'user_id'),
    Index('ix_user_roles_role', 'role_id'),
    extend_existing=True
)

# Association table for Task-Tag many-to-many relationship
task_tags = Table(
    'task_tags',
    Base.metadata,
    Column(
        'task_id',
        Integer,
        ForeignKey('tasks.id', ondelete="CASCADE",
                   name='fk_task_tags_task_id'),
        primary_key=True
    ),
    Column(
        'tag_id',
        Integer,
        ForeignKey('tags.id', ondelete="CASCADE", name='fk_task_tags_tag_id'),
        primary_key=True
    ),
    Column('created_at', DateTime(timezone=True), server_default=func.now()),
    UniqueConstraint('task_id', 'tag_id', name='uq_task_tags'),
    Index('ix_task_tags_task', 'task_id'),
    Index('ix_task_tags_tag', 'tag_id'),
    extend_existing=True
)

# Add more association tables here as needed
