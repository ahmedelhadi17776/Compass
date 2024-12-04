"""Authentication service module."""
from datetime import datetime, timedelta, timezone
import secrets
import logging
from typing import Optional, Dict, Any, List
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt
import re
from src.utils.datetime_utils import utc_now

from src.core.config import settings
from src.data.database.models import User, PasswordReset, UserSession
from src.data.database.session import get_db
from src.services.authentication.jwt_handler import create_access_token
from src.utils.security import get_password_hash, verify_password, generate_secure_token

# Configure logging
logger = logging.getLogger("auth")
logger.setLevel(logging.INFO)

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class WeakPasswordError(Exception):
    """Exception raised when password does not meet strength requirements."""
    def __init__(self, message: str = "Password does not meet strength requirements"):
        self.message = message
        super().__init__(self.message)

def validate_password_strength(password: str) -> None:
    """Validate password strength against requirements."""
    if len(password) < settings.MIN_PASSWORD_LENGTH:
        raise WeakPasswordError(f"Password must be at least {settings.MIN_PASSWORD_LENGTH} characters long")
    
    if settings.PASSWORD_REQUIRE_UPPERCASE and not any(c.isupper() for c in password):
        raise WeakPasswordError("Password must contain at least one uppercase letter")
    
    if settings.PASSWORD_REQUIRE_LOWERCASE and not any(c.islower() for c in password):
        raise WeakPasswordError("Password must contain at least one lowercase letter")
    
    if settings.PASSWORD_REQUIRE_DIGITS and not any(c.isdigit() for c in password):
        raise WeakPasswordError("Password must contain at least one digit")
    
    if settings.PASSWORD_REQUIRE_SPECIAL and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        raise WeakPasswordError("Password must contain at least one special character")

class AuthService:
    """Authentication service class."""

    def __init__(self, db: AsyncSession):
        """Initialize AuthService with database session."""
        self.db = db
        logger.info("AuthService initialized")

    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify an access token."""
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

    async def verify_session(self, token: str) -> Dict[str, Any]:
        """Verify a session token."""
        try:
            payload = self.verify_token(token)
            session_token = payload.get("session")
            if session_token:
                session = await self.db.execute(
                    select(UserSession).filter(
                        and_(
                            UserSession.session_token == session_token,
                            UserSession.is_active == True,
                            UserSession.expires_at > utc_now()
                        )
                    )
                )
                session = session.scalar_one_or_none()
                
                if not session:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid or expired session"
                    )
                
                # Update last activity
                session.last_activity = utc_now()
                await self.refresh_session(session)
            
            return payload
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate token"
            )

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        result = await self.db.execute(select(User).filter(User.email == email))
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        result = await self.db.execute(select(User).filter(User.id == user_id))
        return result.scalar_one_or_none()

    async def validate_password_strength(self, password: str) -> None:
        """Validate password strength asynchronously."""
        if not password:
            raise WeakPasswordError("Password cannot be empty")
            
        validate_password_strength(password)

    async def create_session(self, user_id: int) -> UserSession:
        """Create a new user session."""
        session = UserSession(
            user_id=user_id,
            session_token=secrets.token_urlsafe(32),
            expires_at=utc_now() + timedelta(days=settings.SESSION_EXPIRE_DAYS),
            is_active=True
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def validate_session(self, session_token: str) -> Optional[UserSession]:
        """Validate a session token."""
        if not session_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid session"
            )

        result = await self.db.execute(
            select(UserSession).where(
                and_(
                    UserSession.session_token == session_token,
                    UserSession.is_active == True,
                    UserSession.expires_at > utc_now()
                )
            )
        )
        session = result.scalar_one_or_none()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid session"
            )

        if session.expires_at <= utc_now():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session has expired"
            )

        return session

    async def authenticate_user(self, email: str, password: str) -> User:
        """Authenticate a user."""
        # Input validation
        if not email or not password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid credentials"
            )

        if len(email) > 320 or len(password) > 128:  # Standard email max length
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid credentials"
            )

        # Email format validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email format"
            )

        user = await self.get_user_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )

        if not verify_password(password, user.hashed_password):
            await self._handle_failed_login(user)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )

        if user.is_locked:
            if await self._should_unlock_account(user):
                await self._unlock_account(user)
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Account is locked. Please try again later."
                )

        # Update last login
        user.last_login = utc_now()
        user.failed_login_attempts = 0
        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def _handle_failed_login(self, user: User) -> None:
        """Handle failed login attempt."""
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= settings.MAX_FAILED_LOGIN_ATTEMPTS:
            user.is_locked = True
            user.locked_until = utc_now() + timedelta(minutes=settings.LOGIN_BLOCK_DURATION)
        await self.db.commit()
        await self.db.refresh(user)

    async def _should_unlock_account(self, user: User) -> bool:
        """Check if account should be unlocked."""
        if not user.locked_until:
            return True
        return utc_now() > user.locked_until

    async def _unlock_account(self, user: User) -> None:
        """Unlock a user account."""
        user.is_locked = False
        user.locked_until = None
        user.failed_login_attempts = 0
        await self.db.commit()
        await self.db.refresh(user)

    async def _reset_failed_login_attempts(self, user: User) -> None:
        """Reset failed login attempts."""
        user.failed_login_attempts = 0
        await self.db.commit()
        await self.db.refresh(user)

    async def create_user_session(self, user: User) -> UserSession:
        """Create a new user session."""
        # Check for maximum active sessions
        active_sessions = await self.get_user_sessions(user.id)
        if len(active_sessions) >= settings.MAX_SESSIONS_PER_USER:
            oldest_session = min(active_sessions, key=lambda s: s.created_at)
            oldest_session.is_active = False
            await self.db.commit()

        session = UserSession(
            user_id=user.id,
            expires_at=utc_now() + timedelta(days=settings.SESSION_DURATION_DAYS)
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def invalidate_session(self, session_token: str) -> None:
        """Invalidate a user session."""
        session = await self.db.execute(
            select(UserSession).filter(
                and_(
                    UserSession.session_token == session_token,
                    UserSession.is_active == True
                )
            )
        )
        session = session.scalar_one_or_none()
        
        if session:
            session.is_active = False
            session.ended_at = utc_now()
            await self.db.commit()

    async def cleanup_expired_sessions(self) -> None:
        """Clean up expired sessions."""
        try:
            result = await self.db.execute(
                select(UserSession).filter(
                    and_(
                        UserSession.is_active == True,
                        UserSession.expires_at <= utc_now()
                    )
                )
            )
            expired_sessions = result.scalars().all()
            
            for session in expired_sessions:
                session.is_active = False
                session.ended_at = utc_now()
            
            await self.db.commit()
        except Exception as e:
            await self.db.rollback()
            raise e

    async def refresh_session(self, session: UserSession) -> None:
        """Refresh session expiry if within refresh window."""
        try:
            now = utc_now()
            refresh_window = timedelta(minutes=settings.SESSION_REFRESH_WINDOW)
            
            if session.expires_at - now <= refresh_window:
                session.expires_at = now + timedelta(minutes=settings.SESSION_EXPIRE_MINUTES)
                session.last_activity = now
                await self.db.commit()
        except Exception as e:
            await self.db.rollback()
            raise e

    async def get_session(self, session_token: str) -> Optional[UserSession]:
        """Get a session by its token."""
        result = await self.db.execute(
            select(UserSession).filter(
                and_(
                    UserSession.session_token == session_token,
                    UserSession.is_active == True
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_user_sessions(self, user_id: int) -> List[UserSession]:
        """Get all active sessions for a user."""
        result = await self.db.execute(
            select(UserSession).filter(
                and_(
                    UserSession.user_id == user_id,
                    UserSession.is_active == True
                )
            )
        )
        return result.scalars().all()

    async def register_user(self, user_data: dict) -> User:
        """Register a new user."""
        # Check if user with email already exists
        if await self.get_user_by_email(user_data["email"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Validate password strength
        try:
            await self.validate_password_strength(user_data["password"])
        except WeakPasswordError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=e.message
            )

        # Create new user
        user = User(
            email=user_data["email"],
            hashed_password=get_password_hash(user_data["password"]),
            is_active=True
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def create_user_token(self, user: User) -> Dict[str, str]:
        """Create access token for user."""
        session = await self.create_user_session(user)
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={
                "sub": str(user.id),
                "session": session.session_token,
                "type": "access"
            }
        )
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": int(access_token_expires.total_seconds())
        }

    async def create_password_reset_token(self, email: str) -> str:
        """Create a password reset token."""
        user = await self.get_user_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Generate reset token
        reset_token = secrets.token_urlsafe(32)
        expires_at = utc_now() + timedelta(hours=24)
        
        # Create password reset record
        reset = PasswordReset(
            user_id=user.id,
            token=reset_token,
            expires_at=expires_at,
            used=False
        )
        self.db.add(reset)
        await self.db.commit()
        
        return reset_token

    async def reset_password(self, token: str, new_password: str) -> None:
        """Reset user password using reset token."""
        # Validate password strength
        validate_password_strength(new_password)
        
        # Find valid reset token
        reset = await self.db.execute(
            select(PasswordReset).filter(
                and_(
                    PasswordReset.token == token,
                    PasswordReset.used == False,
                    PasswordReset.expires_at > utc_now()
                )
            )
        )
        reset = reset.scalar_one_or_none()
        
        if not reset:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        
        # Update user password
        user = await self.db.get(User, reset.user_id)
        user.hashed_password = get_password_hash(new_password)
        
        # Mark token as used
        reset.used = True
        reset.updated_at = utc_now()
        
        await self.db.commit()

    async def request_password_reset(self, email: str) -> str:
        """
        Request a password reset for a user.
        
        Args:
            email: The email address of the user requesting password reset
            
        Returns:
            str: A success message
            
        Raises:
            HTTPException: If user not found or other errors occur
        """
        async with self.db.begin() as session:
            user = await session.scalar(
                select(User).where(User.email == email)
            )
            if not user:
                raise HTTPException(
                    status_code=404,
                    detail="No user found with this email address"
                )
            
            # Generate reset token
            token = secrets.token_urlsafe(32)
            expires_at = utc_now() + timedelta(hours=24)
            
            # Create password reset record
            reset_record = PasswordReset(
                user_id=user.id,
                token=token,
                expires_at=expires_at
            )
            session.add(reset_record)
            
            # TODO: Send email with reset link
            # For now, just return the token
            return token

    async def verify_password_reset(self, token: str, new_password: str) -> None:
        """
        Verify a password reset token and set the new password.
        
        Args:
            token: The reset token
            new_password: The new password to set
            
        Raises:
            HTTPException: If token is invalid, expired, or other errors occur
        """
        async with self.db.begin() as session:
            reset_record = await session.scalar(
                select(PasswordReset)
                .where(
                    and_(
                        PasswordReset.token == token,
                        PasswordReset.used == False,
                        PasswordReset.expires_at > utc_now()
                    )
                )
            )
            
            if not reset_record:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid or expired reset token"
                )
            
            # Get user and update password
            user = await session.get(User, reset_record.user_id)
            if not user:
                raise HTTPException(
                    status_code=404,
                    detail="User not found"
                )
            
            # Update password and mark token as used
            user.hashed_password = get_password_hash(new_password)
            reset_record.used = True
            reset_record.updated_at = utc_now()

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user from token."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        user_id = int(payload.get("sub"))
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
        
        result = await db.execute(select(User).filter(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User is inactive"
            )
        
        # Verify session if present
        session_token = payload.get("session")
        if session_token:
            result = await db.execute(
                select(UserSession).filter(
                    and_(
                        UserSession.session_token == session_token,
                        UserSession.user_id == user_id,
                        UserSession.is_active == True,
                        UserSession.expires_at > utc_now()
                    )
                )
            )
            session = result.scalar_one_or_none()
            
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired session"
                )
            
            # Update session activity
            session.last_activity = utc_now()
            await db.commit()
        
        return user
        
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )

async def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    """Get AuthService instance."""
    return AuthService(db)
