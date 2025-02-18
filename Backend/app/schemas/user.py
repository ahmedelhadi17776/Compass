from pydantic import BaseModel, EmailStr, validator
from datetime import datetime
from typing import Optional
from Backend.utils.validation_utils import validate_phone_number


class UserBase(BaseModel):
    username: str
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None

    @validator('phone_number')
    def validate_phone(cls, v):
        if v is not None:
            result = validate_phone_number(v)
            if not result["is_valid"]:
                raise ValueError(
                    f"Invalid phone number. Requirements: {result['requirements']}")
            return result["formatted_number"]
        return v


class UserResponse(UserBase):
    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime
    avatar_url: Optional[str] = None
    timezone: Optional[str] = None
    locale: Optional[str] = None
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True  # This replaces orm_mode=True in newer versions of Pydantic


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    avatar_url: Optional[str] = None
    timezone: Optional[str] = None
    locale: Optional[str] = None

    @validator('phone_number')
    def validate_phone(cls, v):
        if v is not None:
            result = validate_phone_number(v)
            if not result["is_valid"]:
                raise ValueError(
                    f"Invalid phone number. Requirements: {result['requirements']}")
            return result["formatted_number"]
        return v

    class Config:
        from_attributes = True
