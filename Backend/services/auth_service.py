from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import HTTPException, status
from Backend.data_layer.repositories.user_repository import UserRepository
from Backend.data_layer.repositories.session_repository import SessionRepository
from Backend.core.config import settings
from Backend.app.schemas.auth import TokenData, UserCreate
from Backend.app.schemas.user import UserResponse, UserUpdate
from Backend.utils.security_utils import hash_password, create_access_token, verify_password
from Backend.data_layer.database.models.user import User
from Backend.data_layer.database.models.session import Session, SessionStatus


class AuthService:
    def __init__(self, user_repository: UserRepository, session_repository: SessionRepository):
        self.user_repository = user_repository
        self.session_repository = session_repository

    def get_password_hash(self, password: str) -> str:
        return hash_password(password)

    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        user = await self.user_repository.get_by_username(username)
        if not user:
            print(f"🔴 User not found: {username}")
            return None

        if not user.is_active:
            print(f"🔴 User account is not active: {username}")
            return None

        if not verify_password(password, user.password_hash):
            print(f"🔴 Invalid password for user: {username}")
            # Update failed login attempts if needed
            return None

        print(f"✅ User authenticated successfully: {username}")
        return user

    async def register_user(self, user_create: UserCreate) -> UserResponse:
        # Check if user exists
        existing_user = await self.user_repository.get_by_username(user_create.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )

        # Hash password and create user
        hashed_password = hash_password(user_create.password)
        user = await self.user_repository.create(
            username=user_create.username,
            email=user_create.email,
            password_hash=hashed_password,
            first_name=user_create.first_name,
            last_name=user_create.last_name,
            is_active=True
        )

        return UserResponse.from_orm(user)

    async def create_session(self, user_id: int, device_info: str = None, ip_address: str = None):
        expires_at = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        token = create_access_token(
            data={"sub": str(user_id)},
            expires_delta=timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )

        return await self.session_repository.create_session(
            user_id=user_id,
            token=token,
            expires_at=expires_at,
            device_info=device_info,
            ip_address=ip_address
        )

    async def validate_session(self, token: str):
        session = await self.session_repository.get_valid_session(token)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired session"
            )
        return session

    async def invalidate_session(self, token: str):
        return await self.session_repository.invalidate_session(token)

    async def get_user_sessions(self, user_id: int):
        return await self.session_repository.get_user_sessions(user_id)

    async def update_user(self, user_id: int, user_data: UserUpdate) -> User:
        """Update user information"""
        # Get existing user
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # If email is being updated, check it's not taken
        if user_data.email and user_data.email != user.email:
            existing_user = await self.user_repository.get_by_email(user_data.email)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )

        # Update user
        try:
            updated_user = await self.user_repository.update(
                user_id=user_id,
                update_data=user_data.model_dump(exclude_unset=True)
            )
            return updated_user
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update user: {str(e)}"
            )
