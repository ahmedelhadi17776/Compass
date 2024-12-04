from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

class TaskBase(BaseModel):
    """Base task schema."""
    model_config = ConfigDict(from_attributes=True)
    
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: Optional[str] = None
    status: Optional[str] = None

class TaskCreate(TaskBase):
    """Task creation schema."""
    model_config = ConfigDict(from_attributes=True)
    pass

class TaskUpdate(TaskBase):
    """Task update schema."""
    model_config = ConfigDict(from_attributes=True)
    
    title: Optional[str] = Field(None, min_length=1, max_length=255)

class TaskResponse(TaskBase):
    """Task response schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    updated_at: datetime
    user_id: int
