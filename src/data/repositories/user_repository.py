"""User repository module."""
from datetime import datetime, timedelta
from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database.models.user import User
from ..database.models.session import Session
from core.security import hash_password, verify_password
from core.exceptions import (
    UserNotFoundError,
    InvalidCredentialsError,
    UserAlreadyExistsError
)

class UserRepository:
    """User repository class."""

    def __init__(self, session: AsyncSession):
        """Initialize user repository."""
        self._session = session

    async def register_user(self, user_data: dict) -> User:
        """Register a new user."""
        # Check if user already exists
        existing_user = await self._session.execute(
            select(User).where(User.email == user_data["email"])
        )
        if existing_user.scalar_one_or_none():
            raise UserAlreadyExistsError(f"User with email {user_data['email']} already exists")

        # Create new user
        hashed_password = hash_password(user_data["password"])
        user = User(
            email=user_data["email"],
            hashed_password=hashed_password,
            full_name=user_data.get("full_name", ""),
            is_active=True,
            is_verified=False
        )
        self._session.add(user)
        await self._session.commit()
        await self._session.refresh(user)
        return user

    async def login_user(self, credentials: dict) -> User:
        """Login a user."""
        user = await self._session.execute(
            select(User).where(User.email == credentials["email"])
        )
        user = user.scalar_one_or_none()
        if not user:
            raise UserNotFoundError(f"User with email {credentials['email']} not found")

        if not verify_password(credentials["password"], user.hashed_password):
            raise InvalidCredentialsError("Invalid password")

        if not user.is_active:
            raise InvalidCredentialsError("User account is not active")

        return user

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        user = await self._session.execute(
            select(User).where(User.id == user_id)
        )
        return user.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        user = await self._session.execute(
            select(User).where(User.email == email)
        )
        return user.scalar_one_or_none()

    async def update_user(self, user_id: int, user_data: dict) -> Optional[User]:
        """Update user."""
        user = await self.get_user_by_id(user_id)
        if not user:
            return None

        for key, value in user_data.items():
            if hasattr(user, key):
                if key == "password":
                    setattr(user, "hashed_password", hash_password(value))
                else:
                    setattr(user, key, value)

        await self._session.commit()
        await self._session.refresh(user)
        return user

    async def delete_user(self, user_id: int) -> bool:
        """Delete user."""
        user = await self.get_user_by_id(user_id)
        if not user:
            return False

        await self._session.delete(user)
        await self._session.commit()
        return True

    async def list_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """List users."""
        users = await self._session.execute(
            select(User)
            .offset(skip)
            .limit(limit)
        )
        return users.scalars().all()

    async def verify_user(self, user_id: int) -> Optional[User]:
        """Verify user."""
        user = await self.get_user_by_id(user_id)
        if not user:
            return None

        user.is_verified = True
        await self._session.commit()
        await self._session.refresh(user)
        return user

    async def deactivate_user(self, user_id: int) -> Optional[User]:
        """Deactivate user."""
        user = await self.get_user_by_id(user_id)
        if not user:
            return None

        user.is_active = False
        await self._session.commit()
        await self._session.refresh(user)
        return user

    async def activate_user(self, user_id: int) -> Optional[User]:
        """Activate user."""
        user = await self.get_user_by_id(user_id)
        if not user:
            return None

        user.is_active = True
        await self._session.commit()
        await self._session.refresh(user)
        return user
