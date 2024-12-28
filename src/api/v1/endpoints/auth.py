"""Authentication endpoints."""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from src.core.security import get_current_user
from src.services.authentication import AuthenticationService
from src.schemas.auth import (
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
    SessionResponse,
    PasswordResetRequest,
    PasswordReset,
    EmailVerificationRequest
)
from src.data.database.models import User
from src.data.database.connection import get_db
from src.services.authentication.auth_service import AuthService

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
    responses={404: {"description": "Not found"}},
)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""
    auth_service = AuthService(db)
    try:
        token = await auth_service.register_user(user)
        return token
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Authenticate user and return token."""
    auth_service = AuthService(db)
    token = await auth_service.authenticate_user(credentials)
    if not token:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return token


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: Request,
    refresh_token: str,
    auth_service: AuthenticationService = Depends()
) -> TokenResponse:
    """Refresh access token using refresh token."""
    new_session = await auth_service.refresh_session(refresh_token)
    return TokenResponse(
        access_token=new_session.session_token,
        refresh_token=new_session.refresh_token,
        token_type="bearer"
    )


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    auth_service: AuthenticationService = Depends()
):
    """Logout user and invalidate current session."""
    await auth_service.end_session(current_user.id)
    return {"message": "Successfully logged out"}


@router.get("/sessions", response_model=List[SessionResponse])
async def get_sessions(
    current_user: User = Depends(get_current_user),
    auth_service: AuthenticationService = Depends()
) -> List[SessionResponse]:
    """Get all active sessions for current user."""
    return await auth_service.get_user_sessions(current_user.id)


@router.post("/sessions/{session_id}/revoke")
async def revoke_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    auth_service: AuthenticationService = Depends()
):
    """Revoke a specific session."""
    session = await auth_service.get_session_by_id(session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    await auth_service.end_session(session.session_token)
    return {"message": "Session revoked successfully"}


@router.post("/password-reset/request")
async def request_password_reset(
    reset_request: PasswordResetRequest,
    auth_service: AuthenticationService = Depends()
):
    """Request password reset token."""
    await auth_service.request_password_reset(reset_request.email)
    return {"message": "If the email exists, a password reset link has been sent"}


@router.post("/password-reset/verify")
async def reset_password(
    reset_data: PasswordReset,
    auth_service: AuthenticationService = Depends()
):
    """Reset password using reset token."""
    await auth_service.reset_password(
        reset_data.token,
        reset_data.new_password
    )
    return {"message": "Password reset successfully"}


@router.post("/email/verify-request")
async def request_email_verification(
    verification_request: EmailVerificationRequest,
    auth_service: AuthenticationService = Depends()
):
    """Request email verification token."""
    await auth_service.request_email_verification(verification_request.email)
    return {"message": "Verification email sent"}


@router.get("/email/verify/{token}")
async def verify_email(
    token: str,
    auth_service: AuthenticationService = Depends()
):
    """Verify email using verification token."""
    await auth_service.verify_email(token)
    return {"message": "Email verified successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
) -> UserResponse:
    """Get current user information."""
    return current_user
