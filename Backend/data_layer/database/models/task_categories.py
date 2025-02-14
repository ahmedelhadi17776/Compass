from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Index
from sqlalchemy.orm import relationship
from data_layer.database.models.base import Base
import datetime


class TaskCategory(Base):
    __tablename__ = "task_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    color_code = Column(String(20))
    icon = Column(String(50))
    parent_id = Column(Integer, ForeignKey("task_categories.id"))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow,
                        onupdate=datetime.datetime.utcnow)

    # Relationships
    tasks = relationship("Task", back_populates="category")
    children = relationship("TaskCategory")

    __table_args__ = (
        Index("ix_task_category_name", "name"),
        Index("ix_task_category_parent_id", "parent_id"),
    )
