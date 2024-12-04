from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from src.data.database.connection import get_db
from src.data.database.models import User
from src.application.schemas.role import (
    Role,
    RoleCreate,
    RoleUpdate,
    RoleWithPermissions
)
from src.services.authorization.role_service import role_service
from src.services.authorization.dependencies import check_permission
from src.services.authentication.auth_service import get_current_user

router = APIRouter(
    prefix="/roles",
    tags=["roles"],
    dependencies=[Depends(get_current_user)]
)

@router.post("/", response_model=Role, status_code=status.HTTP_201_CREATED)
async def create_role(
    role_data: RoleCreate,
    db: Session = Depends(get_db),
    _: User = Depends(check_permission("roles", "create"))
):
    """Create a new role."""
    role_service.db = db
    return role_service.create_role(role_data)

@router.get("/", response_model=List[Role])
async def list_roles(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    _: User = Depends(check_permission("roles", "read"))
):
    """List all roles."""
    role_service.db = db
    return role_service.list_roles(skip, limit)

@router.get("/{role_id}", response_model=RoleWithPermissions)
async def get_role(
    role_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(check_permission("roles", "read"))
):
    """Get a specific role with its permissions."""
    role_service.db = db
    return role_service.get_role(role_id)

@router.put("/{role_id}", response_model=Role)
async def update_role(
    role_id: int,
    role_data: RoleUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(check_permission("roles", "update"))
):
    """Update a role."""
    role_service.db = db
    return role_service.update_role(role_id, role_data)

@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(check_permission("roles", "delete"))
):
    """Delete a role."""
    role_service.db = db
    role_service.delete_role(role_id)
    return None
