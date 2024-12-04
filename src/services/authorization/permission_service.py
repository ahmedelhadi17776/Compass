from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
from fastapi import HTTPException, status
from src.utils.datetime_utils import utc_now

from src.data.database.models import Permission, Role, role_permissions, User
from src.application.schemas.permission import PermissionCreate, PermissionUpdate

class PermissionService:
    def __init__(self, db: Session):
        self.db = db

    def create_permission(self, permission_data: PermissionCreate) -> Permission:
        """Create a new permission."""
        db_permission = Permission(
            name=permission_data.name,
            description=permission_data.description,
            resource=permission_data.resource,
            action=permission_data.action,
            created_at=utc_now(),
            updated_at=utc_now()
        )
        
        try:
            self.db.add(db_permission)
            self.db.commit()
            self.db.refresh(db_permission)
            return db_permission
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Permission with this resource and action already exists"
            )

    def get_permission(self, permission_id: int) -> Optional[Permission]:
        """Get a permission by ID."""
        permission = self.db.query(Permission).filter(Permission.id == permission_id).first()
        if not permission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Permission not found"
            )
        return permission

    def get_permission_by_name(self, name: str) -> Optional[Permission]:
        """Get a permission by name."""
        return self.db.query(Permission).filter(Permission.name == name).first()

    def list_permissions(self, skip: int = 0, limit: int = 10) -> List[Permission]:
        """List all permissions with pagination."""
        return self.db.query(Permission).offset(skip).limit(limit).all()

    def update_permission(self, permission_id: int, permission_data: PermissionUpdate) -> Permission:
        """Update a permission."""
        permission = self.get_permission(permission_id)
        
        if permission_data.name is not None:
            permission.name = permission_data.name
        if permission_data.description is not None:
            permission.description = permission_data.description
        if permission_data.resource is not None:
            permission.resource = permission_data.resource
        if permission_data.action is not None:
            permission.action = permission_data.action
        
        permission.updated_at = utc_now()
        
        try:
            self.db.commit()
            self.db.refresh(permission)
            return permission
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Error updating permission"
            )

    def delete_permission(self, permission_id: int) -> None:
        """Delete a permission."""
        permission = self.get_permission(permission_id)
        try:
            # First delete all role_permission associations
            self.db.execute(
                role_permissions.delete().where(role_permissions.c.permission_id == permission_id)
            )
            
            # Then delete the permission
            self.db.delete(permission)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Error deleting permission"
            )

    def get_user_permissions(self, user_id: int) -> List[Permission]:
        """Get all permissions for a user through their roles."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get all permissions through role_permissions table
        permissions = self.db.query(Permission).join(
            role_permissions,
            role_permissions.c.permission_id == Permission.id
        ).join(
            Role,
            Role.id == role_permissions.c.role_id
        ).filter(
            Role.id == user.role_id
        ).all()
        
        return permissions

    def check_permission(self, user: User, resource: str, action: str) -> bool:
        """Check if a user has a specific permission through their role."""
        if not user.role:
            return False
        
        # Query to check if the user's role has the required permission
        permission_exists = (
            self.db.query(Permission)
            .join(role_permissions, role_permissions.c.permission_id == Permission.id)
            .filter(
                role_permissions.c.role_id == user.role_id,
                Permission.resource == resource,
                Permission.action == action
            )
            .first()
        )
        
        return permission_exists is not None

permission_service = PermissionService(None)  # Will be initialized with DB session in router
