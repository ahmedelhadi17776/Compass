from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from src.data.database.connection import get_db
from src.data.database.models import User
from src.application.schemas.permission import (
    Permission,
    PermissionCreate,
    PermissionUpdate
)
from src.services.authorization.permission_service import permission_service
from src.services.authorization.dependencies import check_permission
from src.services.authentication.auth_service import get_current_user

router = APIRouter(
    prefix="/permissions",
    tags=["permissions"],
    dependencies=[Depends(get_current_user)]
)

@router.post("/", response_model=Permission, status_code=status.HTTP_201_CREATED)
async def create_permission(
    permission_data: PermissionCreate,
    db: Session = Depends(get_db),
    _: User = Depends(check_permission("permissions", "create"))
):
    """Create a new permission."""
    permission_service.db = db
    return permission_service.create_permission(permission_data)

@router.get("/", response_model=List[Permission])
async def list_permissions(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    _: User = Depends(check_permission("permissions", "read"))
):
    """List all permissions."""
    permission_service.db = db
    return permission_service.list_permissions(skip, limit)

@router.get("/{permission_id}", response_model=Permission)
async def get_permission(
    permission_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(check_permission("permissions", "read"))
):
    """Get a specific permission."""
    permission_service.db = db
    return permission_service.get_permission(permission_id)

@router.put("/{permission_id}", response_model=Permission)
async def update_permission(
    permission_id: int,
    permission_data: PermissionUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(check_permission("permissions", "update"))
):
    """Update a permission."""
    permission_service.db = db
    return permission_service.update_permission(permission_id, permission_data)

@router.delete("/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_permission(
    permission_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(check_permission("permissions", "delete"))
):
    """Delete a permission."""
    permission_service.db = db
    permission_service.delete_permission(permission_id)
    return None
