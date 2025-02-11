"""Common validation schemas."""
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr, validator
from datetime import datetime
import re

class PaginationParams(BaseModel):
    """Pagination parameters."""
    page: int = Field(default=1, ge=1, description="Page number")
    per_page: int = Field(default=10, ge=1, le=100, description="Items per page")

class DateTimeRange(BaseModel):
    """Date time range for filtering."""
    start: Optional[datetime] = Field(None, description="Start datetime")
    end: Optional[datetime] = Field(None, description="End datetime")
    
    @validator('end')
    def end_must_be_after_start(cls, v, values):
        """Validate that end datetime is after start datetime."""
        if v and values.get('start') and v < values['start']:
            raise ValueError('end datetime must be after start datetime')
        return v

class SortParams(BaseModel):
    """Sorting parameters."""
    sort_by: str = Field(..., description="Field to sort by")
    order: str = Field(default="asc", regex="^(asc|desc)$", description="Sort order (asc/desc)")

class SearchParams(BaseModel):
    """Search parameters."""
    query: str = Field(..., min_length=1, max_length=100, description="Search query")
    fields: Optional[List[str]] = Field(None, description="Fields to search in")

class IDParams(BaseModel):
    """ID validation."""
    id: int = Field(..., gt=0, description="Resource ID")

class EmailParams(BaseModel):
    """Email validation."""
    email: EmailStr = Field(..., description="Email address")

class PasswordParams(BaseModel):
    """Password validation."""
    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        regex="^(?=.*[a-z])(?=.*[A-Z])(?=.*\\d)(?=.*[@$!%*?&])[A-Za-z\\d@$!%*?&]",
        description="Password must contain at least 8 characters, including uppercase, lowercase, number and special character"
    )

class TokenParams(BaseModel):
    """Token validation."""
    token: str = Field(..., min_length=32, description="Authentication or reset token")

class StatusParams(BaseModel):
    """Status validation."""
    status: str = Field(..., regex="^(active|inactive|pending|completed|cancelled)$", description="Resource status")
