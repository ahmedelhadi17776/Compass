"""Tag model for task categorization."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index, Text
from sqlalchemy.orm import relationship

from ..base import Base
from .task import task_tags
from src.utils.datetime_utils import utc_now

class Tag(Base):
    """Tag model for categorizing tasks."""
    __tablename__ = "tags"
    __table_args__ = (
        Index('idx_tags_name', 'name'),
        Index('idx_tags_created_by', 'created_by'),
        {'extend_existing': True}
    )

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    color_code = Column(String(7))  # Hex color code
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # Relationships
    tasks = relationship("Task", secondary=task_tags, back_populates="tags")
    creator = relationship("User", back_populates="created_tags")
