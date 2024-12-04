from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from src.utils.datetime_utils import utc_now

from src.data.database.models import Role, Permission, role_permissions
from src.application.schemas.role import RoleCreate, RoleUpdate

class RoleService:
    def __init__(self, db: Session):
        self.db = db

    def create_role(self, role_data: RoleCreate) -> Role:
        """Create a new role."""
        db_role = Role(
            name=role_data.name,
            description=role_data.description,
            created_at=utc_now(),
            updated_at=utc_now()
        )
        
        try:
            self.db.add(db_role)
            self.db.commit()
            self.db.refresh(db_role)
            return db_role
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role with this name already exists"
            )

    def get_role(self, role_id: int) -> Optional[Role]:
        """Get a role by ID."""
        role = self.db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found"
            )
        return role

    def get_role_by_name(self, name: str) -> Optional[Role]:
        """Get a role by name."""
        return self.db.query(Role).filter(Role.name == name).first()

    def list_roles(self, skip: int = 0, limit: int = 10) -> List[Role]:
        """List all roles with pagination."""
        return self.db.query(Role).offset(skip).limit(limit).all()

    def update_role(self, role_id: int, role_data: RoleUpdate) -> Role:
        """Update a role."""
        role = self.get_role(role_id)
        
        if role_data.name is not None:
            role.name = role_data.name
        if role_data.description is not None:
            role.description = role_data.description
        
        role.updated_at = utc_now()
        
        try:
            self.db.commit()
            self.db.refresh(role)
            return role
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Error updating role"
            )

    def delete_role(self, role_id: int) -> None:
        """Delete a role."""
        role = self.get_role(role_id)
        try:
            # First delete all role_permission associations
            self.db.execute(
                role_permissions.delete().where(role_permissions.c.role_id == role_id)
            )
            
            # Then delete the role
            self.db.delete(role)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Error deleting role"
            )

    def assign_permission_to_role(self, role_id: int, permission_id: int) -> None:
        """Assign a permission to a role."""
        role = self.get_role(role_id)
        
        # Check if permission exists
        permission = self.db.query(Permission).filter(Permission.id == permission_id).first()
        if not permission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Permission not found"
            )
        
        try:
            # Check if the permission is already assigned to the role
            existing = self.db.query(role_permissions).filter(
                role_permissions.c.role_id == role_id,
                role_permissions.c.permission_id == permission_id
            ).first()
            
            if not existing:
                # Create the association
                self.db.execute(
                    role_permissions.insert().values(
                        role_id=role_id,
                        permission_id=permission_id
                    )
                )
                self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Error assigning permission to role"
            )

    def remove_permission_from_role(self, role_id: int, permission_id: int) -> None:
        """Remove a permission from a role."""
        role = self.get_role(role_id)
        
        try:
            self.db.execute(
                role_permissions.delete().where(
                    role_permissions.c.role_id == role_id,
                    role_permissions.c.permission_id == permission_id
                )
            )
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Error removing permission from role"
            )

    def get_role_permissions(self, role_id: int) -> List[Permission]:
        """Get all permissions assigned to a role."""
        role = self.get_role(role_id)
        
        permissions = self.db.query(Permission).join(
            role_permissions,
            role_permissions.c.permission_id == Permission.id
        ).filter(
            role_permissions.c.role_id == role_id
        ).all()
        
        return permissions

role_service = RoleService(None)  # Will be initialized with DB session in router
