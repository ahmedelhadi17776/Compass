"""Task domain model."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class Task(BaseModel):
    """Task domain model."""
    id: Optional[int] = None
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    status: str = Field(..., pattern="^(TODO|IN_PROGRESS|REVIEW|DONE)$")
    priority: str = Field(..., pattern="^(LOW|MEDIUM|HIGH|URGENT)$")
    created_by_id: int
    assigned_to_id: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    due_date: Optional[datetime] = None
    
    class Config:
        from_attributes = True
