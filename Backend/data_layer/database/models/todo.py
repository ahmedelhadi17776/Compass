from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime, JSON, Enum as SQLAlchemyEnum, Index
from sqlalchemy.orm import relationship
from Backend.data_layer.database.models.base import Base
import datetime
import enum


class TodoPriority(enum.Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TodoStatus(enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class Todo(Base):
    __tablename__ = "todos"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey(
        "users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(SQLAlchemyEnum(TodoStatus), default=TodoStatus.PENDING)
    priority = Column(SQLAlchemyEnum(TodoPriority),
                      default=TodoPriority.MEDIUM)
    due_date = Column(DateTime)
    reminder_time = Column(DateTime)
    is_recurring = Column(Boolean, default=False)
    # For recurring todos (daily, weekly, etc.)
    recurrence_pattern = Column(JSON)
    tags = Column(JSON)  # Custom tags for organization
    checklist = Column(JSON)  # Sub-items or checklist
    linked_task_id = Column(Integer, ForeignKey(
        "tasks.id", ondelete="SET NULL"))  # Optional link to main task
    linked_calendar_event_id = Column(Integer, ForeignKey(
        "calendar_events.id", ondelete="SET NULL"))
    ai_generated = Column(Boolean, default=False)
    ai_suggestions = Column(JSON)  # AI-generated insights or suggestions
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow,
                        onupdate=datetime.datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="todos")
    linked_task = relationship("Task", foreign_keys=[linked_task_id])
    linked_calendar_event = relationship(
        "CalendarEvent", foreign_keys=[linked_calendar_event_id])
    history = relationship(
        "TodoHistory", back_populates="todo", cascade="all, delete-orphan")

    @property
    def completion_date(self):
        return self._completion_date

    @completion_date.setter
    def completion_date(self, value):
        if isinstance(value, datetime.datetime):
            self._completion_date = value
        else:
            raise ValueError("completion_date must be a datetime object")

    _completion_date = Column(DateTime)

    __table_args__ = (
        Index("ix_todos_user_id", "user_id"),
        Index("ix_todos_status", "status"),
        Index("ix_todos_due_date", "due_date"),
        Index("ix_todos_priority", "priority"),
        Index("ix_todos_created_at", "created_at"),
    )

    def to_dict(self):
        """Convert the todo object to a dictionary for JSON serialization."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'description': self.description,
            'status': self.status.value if hasattr(self, 'status') and self.status else None,
            'priority': self.priority.value if hasattr(self, 'priority') and self.priority else None,
            'due_date': self.due_date.isoformat() if hasattr(self, 'due_date') and self.due_date else None,
            'reminder_time': self.reminder_time.isoformat() if hasattr(self, 'reminder_time') and self.reminder_time else None,
            'is_recurring': self.is_recurring,
            'recurrence_pattern': self.recurrence_pattern if hasattr(self, 'recurrence_pattern') else None,
            'tags': self.tags if hasattr(self, 'tags') else None,
            'checklist': self.checklist if hasattr(self, 'checklist') else None,
            'linked_task_id': self.linked_task_id if hasattr(self, 'linked_task_id') else None,
            'linked_calendar_event_id': self.linked_calendar_event_id if hasattr(self, 'linked_calendar_event_id') else None,
            'ai_generated': self.ai_generated if hasattr(self, 'ai_generated') else False,
            'ai_suggestions': self.ai_suggestions if hasattr(self, 'ai_suggestions') else None,
            'completion_date': self.completion_date.isoformat() if hasattr(self, 'completion_date') and self.completion_date else None,
            'created_at': self.created_at.isoformat() if hasattr(self, 'created_at') and self.created_at else None,
            'updated_at': self.updated_at.isoformat() if hasattr(self, 'updated_at') and self.updated_at else None
        }


class TodoHistory(Base):
    __tablename__ = "todo_history"

    id = Column(Integer, primary_key=True, index=True)
    todo_id = Column(Integer, ForeignKey(
        "todos.id", ondelete="CASCADE"), nullable=False)
    field = Column(String(100))  # Which field was changed
    old_value = Column(Text)
    new_value = Column(Text)
    is_ai_change = Column(Boolean, default=False)
    ai_reasoning = Column(Text)  # If changed by AI, why?
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    todo = relationship("Todo", back_populates="history")
