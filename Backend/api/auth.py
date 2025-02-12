from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from datetime import timedelta
from jose import jwt, JWTError
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

from Backend.schemas.auth import UserCreate, Token, UserResponse, PasswordResetRequest, PasswordResetVerify, PasswordResetResponse
from Backend.services.authentication.auth_service import (
    AuthService, 
    get_auth_service, 
    WeakPasswordError,
    get_current_user
)
from Backend.data.database.connection import get_db
from Backend.core.config import settings
from Backend.data.database.models import User

# Initialize OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Register a new user."""
    try:
        user = auth_service.create_user(user_data)
        return auth_service.create_user_token(user, refresh=True)
    except WeakPasswordError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error during registration"
        )

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Login user and return access token."""
    try:
        return await auth_service.login(form_data.username, form_data.password)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/logout")
async def logout(
    auth_service: AuthService = Depends(get_auth_service),
    token: str = Depends(oauth2_scheme)
):
    """Logout current user."""
    await auth_service.logout(token)
    return {"message": "Successfully logged out"}

@router.get("/me", response_model=UserResponse)
async def read_current_user(
    current_user: User = Depends(get_current_user)
):
    """Get current authenticated user."""
    return current_user

@router.post("/refresh", response_model=Token)
async def refresh_token(
    auth_service: AuthService = Depends(get_auth_service),
    current_user = Depends(get_current_user)
):
    """Refresh access token."""
    return auth_service.create_user_token(current_user, refresh=True)

@router.post("/change-password")
async def change_password(
    current_password: str,
    new_password: str,
    auth_service: AuthService = Depends(get_auth_service),
    current_user = Depends(get_current_user)
):
    """Change user password."""
    if not auth_service.verify_password(current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect password"
        )
    
    current_user.hashed_password = auth_service.get_password_hash(new_password)
    auth_service.db.commit()
    return {"message": "Password updated successfully"}

@router.post("/password-reset/request", response_model=PasswordResetResponse)
async def request_password_reset(
    request: PasswordResetRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Request a password reset token.
    The token will be sent to the user's email address.
    """
    token = await auth_service.request_password_reset(request.email)
    return PasswordResetResponse(
        message="If an account exists with this email, a password reset link has been sent."
    )

@router.post("/password-reset/verify", response_model=PasswordResetResponse)
async def verify_password_reset(
    request: PasswordResetVerify,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Verify a password reset token and set the new password.
    """
    await auth_service.verify_password_reset(request.token, request.new_password)
    return PasswordResetResponse(
        message="Password has been successfully reset"
    )

@router.post("/forgot-password")
async def forgot_password(
    email: str,
    auth_service: AuthService = Depends(get_auth_service)
) -> Dict[str, str]:
    """Request a password reset token."""
    success, message = auth_service.create_password_reset_token(email)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    return {"message": message}

@router.post("/reset-password")
async def reset_password(
    token: str,
    new_password: str,
    auth_service: AuthService = Depends(get_auth_service)
) -> Dict[str, str]:
    """Reset password using a valid token."""
    success, message = auth_service.reset_password(token, new_password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    return {"message": message}

@router.post("/reset-password-request")
async def reset_password_request(
    email: str,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Request password reset."""
    user = auth_service.db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # In a real implementation, you would:
    # 1. Generate a reset token
    # 2. Send it to the user's email
    # 3. Store the token with an expiration time
    reset_token = auth_service.create_access_token(
        data={"sub": user.username, "reset": True},
        expires_delta=timedelta(minutes=15)
    )
    
    return {
        "message": "Password reset instructions sent",
        "reset_token": reset_token  # In production, don't return this
    }

@router.post("/reset-password-confirm")
async def reset_password_confirm(
    token: str,
    new_password: str,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Confirm password reset."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username = payload.get("sub")
        if not username or not payload.get("reset"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid reset token"
            )
        
        user = auth_service.get_user(username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user.hashed_password = auth_service.get_password_hash(new_password)
        auth_service.db.commit()
        return {"message": "Password reset successful"}
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
