"""Association tables for many-to-many relationships."""
from sqlalchemy import Column, Integer, ForeignKey, Table, Index, PrimaryKeyConstraint
from sqlalchemy.ext.declarative import declarative_base

from .base import Base


Base = declarative_base()

# Task-Tag association
task_tags = Table(
    'task_tags',
    Base.metadata,
    Column('task_id', Integer, ForeignKey('Task.id', ondelete='CASCADE'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('Tag.id', ondelete='CASCADE'), primary_key=True),
    PrimaryKeyConstraint("task_id", "tag_id", name="pk_task_tags"),
    Index('ix_task_tags_task_id', 'task_id'),
    Index('ix_task_tags_tag_id', 'tag_id'),
    Index('ix_task_tags_composite', 'task_id', 'tag_id', unique=True),
    extend_existing=True
)
