"""Test cases for authentication service."""
import pytest
from datetime import datetime, timedelta
from fastapi import HTTPException
from sqlalchemy import select

from Backend.data.database.models import User, PasswordReset, UserSession
from Backend.services.authentication.auth_service import AuthService
from Backend.utils.security import get_password_hash, verify_password, generate_secure_token

@pytest.fixture
def auth_service(db_session):
    """Create an auth service instance for testing."""
    return AuthService(db_session)

@pytest.fixture
async def test_user_session(db_session, test_user):
    """Create a test user session."""
    session = UserSession(
        user_id=test_user.id,
        session_token=secrets.token_urlsafe(32),
        expires_at=datetime.now() + timedelta(days=1),
        is_active=True
    )
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)
    return session

@pytest.mark.asyncio
class TestAuthService:
    """Test authentication service."""

    async def test_authenticate_user_success(self, auth_service: AuthService, test_user: User):
        """Test successful user authentication."""
        user = await auth_service.authenticate_user("test@example.com", "testpassword123")
        assert user is not None
        assert user.email == "test@example.com"
        assert user.is_active is True
        assert user.failed_login_attempts == 0

    async def test_authenticate_user_wrong_password(self, auth_service: AuthService, test_user: User):
        """Test authentication with wrong password."""
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.authenticate_user("test@example.com", "wrongpassword")
        assert exc_info.value.status_code == 401
        assert "Incorrect email or password" in str(exc_info.value.detail)
        
        # Check failed login attempts increased
        user = await auth_service.db.get(User, test_user.id)
        assert user.failed_login_attempts == 1

    async def test_create_access_token(self, auth_service: AuthService, test_user: User):
        """Test access token creation."""
        token_data = {
            "sub": str(test_user.id),
            "email": test_user.email
        }
        token = auth_service.create_access_token(token_data)
        assert token is not None
        
        # Verify token
        decoded = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        assert decoded["sub"] == str(test_user.id)
        assert decoded["email"] == test_user.email
        assert "exp" in decoded

    async def test_verify_token(self, auth_service: AuthService, test_user: User):
        """Test token verification."""
        token_data = {
            "sub": str(test_user.id),
            "email": test_user.email
        }
        token = auth_service.create_access_token(token_data)
        
        # Verify valid token
        payload = auth_service.verify_token(token)
        assert payload["sub"] == str(test_user.id)
        assert payload["email"] == test_user.email

    async def test_verify_expired_token(self, auth_service: AuthService, test_user: User):
        """Test verification of expired token."""
        token_data = {
            "sub": str(test_user.id),
            "email": test_user.email,
            "exp": datetime.now() - timedelta(minutes=1)
        }
        expired_token = jwt.encode(token_data, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        
        with pytest.raises(HTTPException) as exc_info:
            auth_service.verify_token(expired_token)
        assert exc_info.value.status_code == 401
        assert "Token has expired" in str(exc_info.value.detail)

    async def test_account_locking(self, auth_service: AuthService, test_user: User):
        """Test account locking after multiple failed attempts."""
        # Attempt login with wrong password multiple times
        for _ in range(settings.MAX_FAILED_LOGIN_ATTEMPTS):
            with pytest.raises(HTTPException):
                await auth_service.authenticate_user("test@example.com", "wrongpassword")
        
        # Verify account is locked
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.authenticate_user("test@example.com", "testpassword123")
        assert exc_info.value.status_code == 401
        assert "Account is locked" in str(exc_info.value.detail)
        
        # Verify user state
        user = await auth_service.db.get(User, test_user.id)
        assert user.failed_login_attempts == settings.MAX_FAILED_LOGIN_ATTEMPTS
        assert user.locked_until is not None

    async def test_session_management(self, auth_service: AuthService, test_user: User, test_user_session: UserSession):
        """Test session management functionality."""
        # Test active session verification
        session = await auth_service.verify_session(test_user_session.session_token)
        assert session is not None
        assert session.is_active is True
        
        # Test session invalidation
        await auth_service.invalidate_session(test_user_session.session_token)
        
        # Verify session is inactive
        session = await auth_service.db.get(UserSession, test_user_session.id)
        assert session.is_active is False

    async def test_password_reset(self, auth_service: AuthService, test_user: User):
        """Test password reset functionality."""
        # Generate reset token
        reset_token = await auth_service.create_password_reset_token(test_user.email)
        assert reset_token is not None
        
        # Verify token exists in database
        reset = await auth_service.db.execute(
            select(PasswordReset).filter_by(user_id=test_user.id, used=False)
        )
        reset = reset.scalar_one()
        assert reset is not None
        assert reset.token == reset_token
        
        # Reset password
        new_password = "NewPassword123!"
        await auth_service.reset_password(reset_token, new_password)
        
        # Verify new password works
        user = await auth_service.authenticate_user(test_user.email, new_password)
        assert user is not None
        assert user.id == test_user.id