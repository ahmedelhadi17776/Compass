from typing import Optional, Dict
from datetime import datetime
from pydantic import BaseModel, EmailStr, constr

class TokenData(BaseModel):
    username: Optional[str] = None
    exp: Optional[int] = None

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenResponse(Token):
    refresh_token: str
    expires_at: datetime

class UserBase(BaseModel):
    username: constr(min_length=3, max_length=50)
    email: EmailStr
    full_name: constr(min_length=1, max_length=100)

class UserCreate(UserBase):
    password: constr(min_length=8, max_length=100)

    class Config:
        json_schema_extra = {
            "example": {
                "username": "johndoe",
                "email": "john@example.com",
                "full_name": "John Doe",
                "password": "StrongP@ss123"
            }
        }

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    is_admin: bool = False

    class Config:
        from_attributes = True

class SessionResponse(BaseModel):
    id: int
    device_info: Dict
    ip_address: str
    created_at: datetime
    last_activity: datetime
    is_active: bool

    class Config:
        from_attributes = True

class EmailVerificationRequest(BaseModel):
    email: EmailStr

class PasswordResetRequest(BaseModel):
    """Schema for requesting a password reset."""
    email: EmailStr

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com"
            }
        }

class PasswordResetVerify(BaseModel):
    """Schema for verifying a password reset token and setting new password."""
    token: str
    new_password: constr(min_length=8, max_length=100)

    class Config:
        json_schema_extra = {
            "example": {
                "token": "reset_token_here",
                "new_password": "NewStrongP@ss123"
            }
        }

class PasswordResetResponse(BaseModel):
    """Schema for password reset response."""
    message: str
    email: EmailStr

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Password reset email sent successfully",
                "email": "user@example.com"
            }
        }

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: constr(min_length=8, max_length=100)

class PasswordChange(BaseModel):
    current_password: str
    new_password: constr(min_length=8, max_length=100)
