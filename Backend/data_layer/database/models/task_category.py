from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
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
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    tasks = relationship("Task", back_populates="category")
    organization = relationship("Organization", back_populates="task_categories")
    parent = relationship("TaskCategory", remote_side=[id], backref="subcategories") 