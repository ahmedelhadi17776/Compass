from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime

class PermissionBase(BaseModel):
    """Base permission schema."""
    model_config = ConfigDict(from_attributes=True)
    
    name: str = Field(..., description="Name of the permission", min_length=1, max_length=50)
    description: Optional[str] = Field(None, description="Description of what the permission allows")
    resource: str = Field(..., description="The resource this permission applies to (e.g., 'users', 'tasks')", min_length=1, max_length=50)
    action: str = Field(..., description="The action allowed (e.g., 'create', 'read', 'update', 'delete')", min_length=1, max_length=50)

class PermissionCreate(PermissionBase):
    """Permission creation schema."""
    model_config = ConfigDict(from_attributes=True)
    pass

class Permission(PermissionBase):
    """Permission response schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    updated_at: datetime

class PermissionUpdate(BaseModel):
    """Permission update schema."""
    model_config = ConfigDict(from_attributes=True)
    
    name: Optional[str] = Field(None, description="Name of the permission", min_length=1, max_length=50)
    description: Optional[str] = Field(None, description="Description of what the permission allows")
    resource: Optional[str] = Field(None, description="The resource this permission applies to (e.g., 'users', 'tasks')", min_length=1, max_length=50)
    action: Optional[str] = Field(None, description="The action allowed (e.g., 'create', 'read', 'update', 'delete')", min_length=1, max_length=50)

class PermissionInRole(Permission):
    role_id: int
