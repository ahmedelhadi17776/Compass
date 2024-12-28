from pydantic import BaseModel, Field
from typing import List, Optional


class PermissionCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=50)
    description: Optional[str] = None
    resource: str = Field(..., min_length=3, max_length=50)
    action: str = Field(..., min_length=3, max_length=50)


class PermissionResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    resource: str
    action: str

    class Config:
        orm_mode = True


class RoleCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=50)
    description: Optional[str] = None
    permissions: List[str]  # List of permission names


class RoleResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    permissions: List[PermissionResponse]

    class Config:
        orm_mode = True
