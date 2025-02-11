"""To-Do model for task management."""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base


class Todo(Base):
    """Model for managing to-do tasks."""
    __tablename__ = "todos"
    __table_args__ = (
        Index('ix_todos_user', 'user_id'),
        Index('ix_todos_status', 'status'),
        {'extend_existing': True}
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey(
        "users.id", ondelete='CASCADE'), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(String(500))
    # e.g., 'pending', 'completed'
    status = Column(String(50), default='pending')
    due_date = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="todos")

    def __repr__(self):
        return f"<Todo(id={self.id}, title='{self.title}', status='{self.status}')>"
