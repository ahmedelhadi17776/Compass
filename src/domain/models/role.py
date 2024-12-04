"""Role domain model."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class Role(BaseModel):
    """Role domain model."""
    id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=200)
    permissions: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
