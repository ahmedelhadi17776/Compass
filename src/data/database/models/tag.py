"""Tag and categorization models."""
from datetime import datetime
from enum import Enum
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey,
    Text, JSON, Index, Enum as SQLAEnum, Boolean
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .associations import task_tags  # Import the task_tags table
from .base import Base


class TagType(str, Enum):
    """Tag type enum."""
    SYSTEM = "system"
    USER = "user"
    CATEGORY = "category"
    LABEL = "label"
    STATUS = "status"


class Tag(Base):
    """Tag model for categorization."""
    __tablename__ = "tags"
    __table_args__ = (
        Index('ix_tags_name', 'name'),
        Index('ix_tags_type', 'tag_type'),
        Index('ix_tags_created_by', 'created_by'),
        {'extend_existing': True}
    )

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    tag_type = Column(SQLAEnum(TagType), nullable=False, default=TagType.USER)

    # Styling
    color = Column(String(7))  # Hex color code
    icon = Column(String(50))  # Icon identifier

    # Metadata
    extra_metadata = Column(JSON)  # Additional tag properties
    parent_id = Column(Integer, ForeignKey('tags.id'))  # For hierarchical tags
    order = Column(Integer, default=0)  # For custom ordering
    is_public = Column(Boolean, default=True)

    # Ownership
    created_by = Column(Integer, ForeignKey("users.id", name='fk_tag_user_id'))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __init__(self):
        self.tasks = relationship(
            "Task",
            secondary="task_tags",  # Use the table name as a string
            back_populates="tags"
        )

    # Relationships
    creator = relationship("User", back_populates="created_tags")
    parent = relationship("Tag", remote_side=[id], backref="children")
    tasks = relationship("Task", secondary=task_tags, back_populates="tags")

    def __repr__(self):
        return f"<Tag(id={self.id}, name='{self.name}', type={self.tag_type})>"

    @property
    def full_path(self):
        """Get the full hierarchical path of the tag."""
        if self.parent:
            return f"{self.parent.full_path}/{self.name}"
        return self.name
