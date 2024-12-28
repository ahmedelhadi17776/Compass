from typing import Optional, Callable, List
from functools import wraps
from fastapi import Depends, HTTPException, status
from src.data.database.connection import get_db
from src.data.database.models import User
from src.services.authentication.auth_service import get_current_user
from src.services.authorization.permission_service import permission_service
from src.services.authorization.role_service import RoleService
from sqlalchemy.orm import Session


def check_permission(resource: str, action: str):
    """Dependency for checking if a user has permission to perform an action on a resource."""
    async def permission_dependency(
        current_user: User = Depends(get_current_user),
        db=Depends(get_db)
    ):
        # Initialize permission service with DB session
        permission_service.db = db

        if not permission_service.check_permission(current_user, resource, action):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not authorized to {action} {resource}"
            )
        return current_user
    return permission_dependency


def require_permission(resource: str, action: str):
    """Decorator for requiring specific permissions."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get current user and db from kwargs
            current_user = kwargs.get('current_user')
            db = kwargs.get('db')

            if not current_user or not db:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Missing required dependencies"
                )

            # Initialize permission service with DB session
            permission_service.db = db

            if not permission_service.check_permission(current_user, resource, action):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Not authorized to {action} {resource}"
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator


def get_role_service(db: Session = Depends(get_db)) -> RoleService:
    """Provide RoleService dependency."""
    return RoleService(db)


def require_role(required_roles: List[str]):
    """Dependency to require specific user roles."""

    async def role_dependency(user: User = Depends(get_current_user), role_service: RoleService = Depends(get_role_service)):
        user_roles = [role.name for role in user.roles]
        if not any(role in required_roles for role in user_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not permitted."
            )
        return True

    return role_dependency
