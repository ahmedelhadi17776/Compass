"""Authentication schemas."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, constr, validator, field_validator, ConfigDict
from pydantic import ValidationError
from fastapi import HTTPException
from fastapi import status
import re

__all__ = [
    'UserCreate',
    'Token',
    'TokenData',
    'UserResponse',
    'PasswordResetRequest',
    'PasswordResetVerify',
    'PasswordResetResponse'
]

def validate_password(password: str) -> str:
    """Validate password complexity."""
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long")
    if not any(c.isupper() for c in password):
        raise ValueError("Password must contain at least one uppercase letter")
    if not any(c.islower() for c in password):
        raise ValueError("Password must contain at least one lowercase letter")
    if not any(c.isdigit() for c in password):
        raise ValueError("Password must contain at least one number")
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', password):
        raise ValueError("Password must contain at least one special character")
    return password

class UserBase(BaseModel):
    """Base user schema with common attributes."""
    model_config = ConfigDict(from_attributes=True)
    
    username: constr(min_length=3, max_length=50)
    email: EmailStr

class UserCreate(UserBase):
    """Schema for user registration."""
    model_config = ConfigDict(from_attributes=True)
    
    password: str
    full_name: str

    @field_validator('password')
    @classmethod
    def validate_password_complexity(cls, v):
        try:
            return validate_password(v)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

class UserLogin(BaseModel):
    """Schema for user login."""
    model_config = ConfigDict(from_attributes=True)
    
    username: str
    password: str

class UserResponse(BaseModel):
    """Schema for user response data."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    username: str
    email: EmailStr
    full_name: str

class Token(BaseModel):
    """Schema for authentication token."""
    model_config = ConfigDict(from_attributes=True)
    
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """Schema for token payload data."""
    model_config = ConfigDict(from_attributes=True)
    
    username: str | None = None

class PasswordResetRequest(BaseModel):
    """Schema for password reset request"""
    model_config = ConfigDict(from_attributes=True)
    
    email: EmailStr

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com"
            }
        }

class PasswordResetVerify(BaseModel):
    """Schema for password reset verification"""
    model_config = ConfigDict(from_attributes=True)
    
    token: str
    new_password: str

    class Config:
        json_schema_extra = {
            "example": {
                "token": "reset-token-xyz",
                "new_password": "newSecurePassword123!"
            }
        }

class PasswordResetResponse(BaseModel):
    """Schema for password reset response"""
    model_config = ConfigDict(from_attributes=True)
    
    message: str
