"""User domain model."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field

class User(BaseModel):
    """User domain model."""
    id: Optional[int] = None
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=100)
    hashed_password: Optional[str] = None
    is_active: bool = True
    is_verified: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    roles: List[str] = Field(default_factory=list)
    
    class Config:
        from_attributes = True
