"""User related schemas."""
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime

class UserBase(BaseModel):
    """Base user schema."""
    model_config = ConfigDict(from_attributes=True)
    
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    
class UserCreate(UserBase):
    """User creation schema."""
    model_config = ConfigDict(from_attributes=True)
    
    password: str = Field(..., min_length=8)
    confirm_password: str

class UserUpdate(BaseModel):
    """User update schema."""
    model_config = ConfigDict(from_attributes=True)
    
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    
class UserResponse(UserBase):
    """User response schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    
class TokenData(BaseModel):
    """Token data schema."""
    model_config = ConfigDict(from_attributes=True)
    
    user_id: int
    token_type: str
    exp: datetime
    session_id: Optional[str] = None

class Token(BaseModel):
    """Token schema."""
    model_config = ConfigDict(from_attributes=True)
    
    access_token: str
    token_type: str
    expires_in: int

class UserList(BaseModel):
    """User list schema with pagination."""
    model_config = ConfigDict(from_attributes=True)
    
    users: List[UserResponse]
    total: int
    page: int
    page_size: int
