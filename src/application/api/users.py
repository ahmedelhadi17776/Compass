"""User management routes."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ...dependencies import get_db, get_auth_service, get_current_user
from ...data.database.models import User
from ...application.schemas.user import UserResponse, UserUpdate, UserList
from ...services.authentication.auth_service import AuthService

router = APIRouter(prefix="/api/users", tags=["Users"])

@router.get("/", response_model=UserList)
async def list_users(
    skip: int = 0,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
) -> UserList:
    """List users with pagination."""
    # TODO: Add role-based access control
    users, total = auth_service.list_users(skip=skip, limit=limit)
    return UserList(
        users=users,
        total=total,
        page=skip // limit + 1,
        page_size=limit
    )

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
) -> UserResponse:
    """Get current user's profile."""
    return UserResponse.from_orm(current_user)

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
) -> UserResponse:
    """Get user by ID."""
    # TODO: Add role-based access control
    user = auth_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return UserResponse.from_orm(user)

@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
) -> UserResponse:
    """Update current user's profile."""
    updated_user = auth_service.update_user(
        user=current_user,
        update_data=user_data.dict(exclude_unset=True)
    )
    return UserResponse.from_orm(updated_user)

@router.delete("/me")
async def deactivate_current_user(
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
) -> dict:
    """Deactivate current user's account."""
    auth_service.deactivate_user(current_user)
    return {"message": "Account deactivated successfully"}
