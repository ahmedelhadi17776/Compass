from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict

class OrganizationBase(BaseModel):
    name: str
    description: Optional[str] = None

class OrganizationCreate(OrganizationBase):
    pass

class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class OrganizationResponse(OrganizationBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class OrganizationWithDetails(OrganizationResponse):
    projects_count: Optional[int] = 0
    users_count: Optional[int] = 0
    tasks_count: Optional[int] = 0
    workflows_count: Optional[int] = 0

    class Config:
        from_attributes = True