from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict

class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    organization_id: int

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class ProjectMemberBase(BaseModel):
    user_id: int
    role: str

class ProjectMemberCreate(ProjectMemberBase):
    pass

class ProjectMemberResponse(ProjectMemberBase):
    project_id: int
    joined_at: datetime

    class Config:
        from_attributes = True

class ProjectResponse(ProjectBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ProjectWithDetails(ProjectResponse):
    members_count: Optional[int] = 0
    tasks_count: Optional[int] = 0
    members: List[ProjectMemberResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True