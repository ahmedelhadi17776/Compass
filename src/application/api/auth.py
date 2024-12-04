from datetime import timedelta
from typing import Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from ...dependencies import get_db, get_auth_service, get_current_user
from ...data.database.models import User
from ...application.schemas.user import UserCreate, UserResponse, TokenResponse
from ...services.authentication.auth_service import AuthService
from ...services.notification_service.email_service import email_service
from ...core.config import settings

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    auth_service: AuthService = Depends(get_auth_service)
) -> UserResponse:
    """Register a new user."""
    try:
        user = auth_service.create_user(user_data)
        
        # Generate verification token
        verification_token = auth_service.create_email_verification_token(user)
        
        # Send verification email
        await email_service.send_verification_email(user.email, verification_token)
        
        return UserResponse.from_orm(user)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    request: Request = None,
    auth_service: AuthService = Depends(get_auth_service)
) -> TokenResponse:
    """Authenticate user and return access token."""
    try:
        user = await auth_service.authenticate_user(form_data.username, form_data.password)
        
        # Create user session
        session = auth_service.create_user_session(user)
        
        # Create access token with session info
        access_token = auth_service.create_access_token(
            data={
                "sub": str(user.id),
                "session": session.session_token
            }
        )
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer"
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while logging in"
        )

@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
) -> Dict[str, str]:
    """Logout user and invalidate current session."""
    try:
        # Get current session token from request
        token = auth_service.verify_token(current_user.token)
        session_token = token.get("session")
        
        if session_token:
            auth_service.invalidate_user_session(session_token)
        
        return {"message": "Successfully logged out"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while logging out"
        )

@router.get("/verify-email/{token}")
async def verify_email(
    token: str,
    auth_service: AuthService = Depends(get_auth_service)
) -> Dict[str, str]:
    """Verify user's email address."""
    try:
        auth_service.verify_email(token)
        return {"message": "Email verified successfully"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while verifying email"
        )

@router.post("/request-password-reset")
async def request_password_reset(
    email: str,
    auth_service: AuthService = Depends(get_auth_service)
) -> Dict[str, str]:
    """Request password reset."""
    try:
        user = auth_service.get_user_by_email(email)
        if user:
            reset_token = auth_service.create_password_reset_token(user)
            await email_service.send_password_reset_email(email, reset_token)
        return {"message": "If an account exists with this email, a password reset link has been sent"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while requesting password reset"
        )

@router.post("/reset-password/{token}")
async def reset_password(
    token: str,
    new_password: str,
    auth_service: AuthService = Depends(get_auth_service)
) -> Dict[str, str]:
    """Reset user's password using reset token."""
    try:
        user_id = auth_service.verify_password_reset_token(token)
        user = auth_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        auth_service.change_password(user, new_password)
        return {"message": "Password reset successful"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while resetting password"
        )

@router.post("/change-password")
async def change_password(
    current_password: str,
    new_password: str,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
) -> Dict[str, str]:
    """Change user's password."""
    try:
        if not auth_service.verify_password(current_password, current_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect current password"
            )
        auth_service.change_password(current_user, new_password)
        return {"message": "Password changed successfully"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while changing password"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
) -> UserResponse:
    """Get current user information."""
    return UserResponse.from_orm(current_user)
