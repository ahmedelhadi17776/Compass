"""Authentication service module."""
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import SecurityContext, PasswordManager
from src.data.database.models.auth import User
from src.data.database.repositories.user_repository import UserRepository
from src.services.security.security_service import SecurityService


class AuthService:
    """Authentication service."""

    def __init__(self, db: AsyncSession, security_context: SecurityContext):
        self.db = db
        self.security_context = security_context
        self.user_repository = UserRepository(db)
        self.password_manager = PasswordManager()
        self.security_service = SecurityService(db, security_context)

    async def authenticate_user(self, username: str, password: str) -> User:
        """Authenticate a user."""
        user = await self.user_repository.get_by_username(username)

        try:
            if not user or not self.password_manager.verify_password(
                password, user.hashed_password
            ):
                await self.security_service.log_auth_event(
                    "login",
                    user.id if user else None,
                    success=False,
                    details={"username": username}
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid username or password"
                )

            if not user.is_active:
                await self.security_service.log_auth_event(
                    "login",
                    user.id,
                    success=False,
                    details={"reason": "inactive_user"}
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User is inactive"
                )

            # Log successful authentication
            await self.security_service.log_auth_event(
                "login",
                user.id,
                success=True
            )

            return user

        except Exception as e:
            # Log any unexpected errors
            await self.security_service.log_security_event(
                event_type="error",
                description=f"Authentication error: {str(e)}",
                metadata={"username": username}
            )
            raise

    async def change_password(
        self,
        user: User,
        current_password: str,
        new_password: str
    ) -> None:
        """Change user password."""
        try:
            # Verify current password
            if not self.password_manager.verify_password(
                current_password, user.hashed_password
            ):
                await self.security_service.log_auth_event(
                    "password_change",
                    user.id,
                    success=False,
                    details={"reason": "invalid_current_password"}
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid current password"
                )

            # Validate new password
            self.password_manager.validate_password(new_password)

            # Update password
            user.hashed_password = self.password_manager.hash_password(
                new_password)
            await self.user_repository.update(user)

            # Log successful password change
            await self.security_service.log_auth_event(
                "password_change",
                user.id,
                success=True
            )

        except Exception as e:
            # Log any unexpected errors
            await self.security_service.log_security_event(
                event_type="error",
                description=f"Password change error: {str(e)}",
                metadata={"user_id": user.id}
            )
            raise
