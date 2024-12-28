from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from src.application.schemas.authorization import RoleCreate, RoleResponse, PermissionCreate, PermissionResponse
from src.services.authorization.role_service import RoleService
from src.services.authorization.permission_service import PermissionService
from src.services.authorization.dependencies import require_role
from src.data.database.connection import get_db

router = APIRouter(
    prefix="/authorization",
    tags=["Authorization"],
    dependencies=[Depends(require_role(["admin"]))],
    responses={404: {"description": "Not found"}},
)


@router.post("/roles", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(role: RoleCreate, db: Session = Depends(get_db)):
    """Create a new role."""
    role_service = RoleService(db)
    try:
        new_role = await role_service.create_role(role.name, role.description, role.permissions)
        return new_role
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))


@router.post("/permissions", response_model=PermissionResponse, status_code=status.HTTP_201_CREATED)
async def create_permission(permission: PermissionCreate, db: Session = Depends(get_db)):
    """Create a new permission."""
    permission_service = PermissionService(db)
    try:
        new_permission = await permission_service.create_permission(permission.name, permission.description, permission.resource, permission.action)
        return new_permission
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))


@router.get("/roles", response_model=List[RoleResponse])
async def list_roles(db: Session = Depends(get_db)):
    """List all roles."""
    role_service = RoleService(db)
    return await role_service.list_roles()


@router.get("/permissions", response_model=List[PermissionResponse])
async def list_permissions(db: Session = Depends(get_db)):
    """List all permissions."""
    permission_service = PermissionService(db)
    return await permission_service.list_permissions()
