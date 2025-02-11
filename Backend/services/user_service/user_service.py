"""User service module."""
from typing import Optional, List, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from Backend.core.security import SecurityContext, PasswordManager
from Backend.data.database.models.auth import User
from Backend.data.database.repositories.user_repository import UserRepository
from Backend.services.security.security_service import SecurityService
from Backend.core.security.events import SecurityEventType


class UserService:
    """User service for managing user operations."""

    def __init__(self, db: AsyncSession, security_context: SecurityContext):
        self.db = db
        self.security_context = security_context
        self.user_repository = UserRepository(db)
        self.security_service = SecurityService(db, security_context)
        self.password_manager = PasswordManager()

    async def create_user(self, user_data: Dict[str, Any]) -> User:
        """Create a new user."""
        try:
            # Validate password
            self.password_manager.validate_password(user_data["password"])

            # Hash password
            user_data["hashed_password"] = self.password_manager.hash_password(
                user_data.pop("password")
            )

            # Create user
            user = await self.user_repository.create(user_data)

            # Log security event
            await self.security_service.log_security_event(
                event_type=SecurityEventType.USER_CREATED,
                description=f"User created: {user.username}",
                metadata={"user_id": user.id}
            )

            return user

        except Exception as e:
            await self.security_service.log_security_event(
                event_type=SecurityEventType.ERROR,
                description=f"User creation failed: {str(e)}",
                metadata={"username": user_data.get("username")}
            )
            raise

    async def update_user(self, user_id: int, update_data: Dict[str, Any]) -> User:
        """Update user details."""
        try:
            user = await self.user_repository.get_by_id(user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )

            # Update user
            updated_user = await self.user_repository.update(user_id, update_data)

            # Log security event
            await self.security_service.log_security_event(
                event_type=SecurityEventType.USER_UPDATED,
                description=f"User updated: {updated_user.username}",
                metadata={
                    "user_id": user_id,
                    "updated_fields": list(update_data.keys())
                }
            )

            return updated_user

        except Exception as e:
            await self.security_service.log_security_event(
                event_type=SecurityEventType.ERROR,
                description=f"User update failed: {str(e)}",
                metadata={"user_id": user_id}
            )
            raise

    async def delete_user(self, user_id: int) -> None:
        """Delete a user."""
        try:
            user = await self.user_repository.get_by_id(user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )

            # Delete user
            await self.user_repository.delete(user_id)

            # Log security event
            await self.security_service.log_security_event(
                event_type=SecurityEventType.USER_DELETED,
                description=f"User deleted: {user.username}",
                metadata={"user_id": user_id}
            )

        except Exception as e:
            await self.security_service.log_security_event(
                event_type=SecurityEventType.ERROR,
                description=f"User deletion failed: {str(e)}",
                metadata={"user_id": user_id}
            )
            raise
