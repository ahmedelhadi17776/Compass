"""User repository module."""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from Backend.data.database.models import User
from .base_repository import BaseRepository
from Backend.data.database.errors import UserAlreadyExistsError, UserNotFoundError, InvalidCredentialsError
from Backend.core.security import hash_password, verify_password

class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get a user by email."""
        stmt = select(User).where(User.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> Optional[User]:
        """Get a user by username."""
        stmt = select(User).where(User.username == username)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def register_user(self, user_data: dict) -> User:
        """Register a new user."""
        # Check if user already exists
        existing_user = await self.session.execute(
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
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def login_user(self, credentials: dict) -> User:
        """Login a user."""
        user = await self.session.execute(
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
