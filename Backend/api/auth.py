from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from Backend.data_layer.database.connection import get_db
from Backend.services.auth_service import AuthService
from Backend.data_layer.repositories.user_repository import UserRepository
from Backend.data_layer.repositories.session_repository import SessionRepository
from Backend.app.schemas.auth import Token, UserCreate, TokenData
from Backend.app.schemas.user import UserResponse
from Backend.data_layer.database.models.session import Session
from Backend.data_layer.database.models.user import User
from Backend.core.config import settings
from Backend.app.schemas.session import SessionResponse

router = APIRouter(tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    user_repo = UserRepository(db)
    session_repo = SessionRepository(db)
    return AuthService(user_repo, session_repo)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service)
) -> User:
    try:
        session = await auth_service.validate_session(token)
        # Remove .value here
        user = await auth_service.user_repository.get_by_id(session.user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/register", response_model=UserResponse, tags=["auth"])
async def register(
    user_data: UserCreate,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Register a new user"""
    return await auth_service.register_user(user_data)


@router.post("/login", response_model=Token, tags=["auth"])
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Login and get access token"""
    user = await auth_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create session with device info - Remove .value here
    session = await auth_service.create_session(
        user_id=user.id,
        device_info=request.headers.get("User-Agent") or "Unknown",
        ip_address=request.client.host if request.client else "Unknown"
    )

    return {
        "access_token": session.token,
        "token_type": "bearer"
    }


@router.post("/logout", tags=["auth"])
async def logout(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Logout and invalidate current session"""
    await auth_service.invalidate_session(token)
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse, tags=["auth"])
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return UserResponse.from_orm(current_user)


@router.get("/sessions", response_model=list[SessionResponse], tags=["auth"])
async def get_user_sessions(
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Get all active sessions for current user"""
    # Remove .value here
    return await auth_service.get_user_sessions(current_user.id)


@router.post("/sessions/{session_id}/revoke", tags=["auth"])
async def revoke_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Revoke a specific session"""
    await auth_service.invalidate_session(session_id)
    return {"message": "Session revoked successfully"}


@router.post("/refresh-token", response_model=Token, tags=["auth"])
async def refresh_token(
    request: Request,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Get a new access token using current valid token"""
    # Remove .value here
    session = await auth_service.create_session(
        user_id=current_user.id,
        device_info=request.headers.get("User-Agent") or "Unknown",
        ip_address=request.client.host if request.client else "Unknown"
    )

    return {
        "access_token": session.token,
        "token_type": "bearer"
    }
