from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext
from data_layer.repositories.user_repository import UserRepository
from data_layer.repositories.session_repository import SessionRepository
from core.config import settings
from app.schemas.auth import TokenData, UserCreate
from app.schemas.user import UserResponse
from utils.security_utils import hash_password, verify_password, create_access_token

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    def __init__(self, user_repository: UserRepository, session_repository: SessionRepository):
        self.user_repository = user_repository
        self.session_repository = session_repository

    async def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return verify_password(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        return hash_password(password)

    async def authenticate_user(self, username: str, password: str):
        user = await self.user_repository.get_by_username(username)
        if not user:
            return False
        if not await self.verify_password(password, user.password_hash):
            return False
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
        hashed_password = self.get_password_hash(user_create.password)
        user = await self.user_repository.create(
            username=user_create.username,
            email=user_create.email,
            password_hash=hashed_password,
            first_name=user_create.first_name,
            last_name=user_create.last_name
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
