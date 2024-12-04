from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from src.application.schemas.auth import Token, UserCreate, UserResponse
from src.data.database.connection import get_db
from src.services.authentication.auth_service import get_auth_service, AuthService, get_current_user
from src.domain.models.user import User

router = APIRouter(
    prefix="/auth",
    tags=["authentication"]
)

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Register a new user."""
    user = auth_service.create_user(user_data)
    return auth_service.create_user_token(user)

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Login user and return access token."""
    return auth_service.login(form_data.username, form_data.password)

@router.post("/refresh", response_model=Token)
async def refresh_token(
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Refresh access token."""
    # Add current timestamp to ensure new token
    return auth_service.create_user_token(current_user, refresh=True)

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current authenticated user."""
    return current_user
