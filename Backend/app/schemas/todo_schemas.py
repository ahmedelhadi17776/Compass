from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum


class TodoPriority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TodoStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class TodoBase(BaseModel):
    user_id: int
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    priority: TodoPriority = TodoPriority.MEDIUM
    due_date: Optional[datetime] = None
    reminder_time: Optional[datetime] = None
    is_recurring: bool = False
    recurrence_pattern: Optional[Dict] = None
    tags: Optional[List[str]] = None
    checklist: Optional[List[Dict]] = None
    linked_task_id: Optional[int] = None
    linked_calendar_event_id: Optional[int] = None


class TodoCreate(TodoBase):
    pass


class TodoUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[TodoStatus] = None
    priority: Optional[TodoPriority] = None
    due_date: Optional[datetime] = None
    reminder_time: Optional[datetime] = None
    is_recurring: Optional[bool] = None
    recurrence_pattern: Optional[Dict] = None
    tags: Optional[List[str]] = None
    checklist: Optional[List[Dict]] = None


class Todo(TodoBase):
    id: int
    status: TodoStatus
    completion_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
