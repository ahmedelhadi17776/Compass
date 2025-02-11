from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from .permission import Permission

class RoleBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    name: str = Field(..., description="Name of the role")
    description: Optional[str] = Field(None, description="Description of what the role represents")

class RoleCreate(RoleBase):
    model_config = ConfigDict(from_attributes=True)
    
    permissions: List[int] = Field([], description="List of permission IDs to assign to the role")

class Role(RoleBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    updated_at: datetime
    permissions: List[Permission] = []

class RoleUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[List[int]] = None  # List of permission IDs

class RoleWithPermissions(Role):
    model_config = ConfigDict(from_attributes=True)
    
    permissions: List[Permission]
