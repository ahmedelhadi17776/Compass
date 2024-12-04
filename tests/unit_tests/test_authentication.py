"""Test authentication functionality."""
import pytest
from datetime import datetime, timedelta
from fastapi import HTTPException
from src.services.authentication import AuthenticationService
from src.data.database.models import User, UserSession

@pytest.fixture
def auth_service(db_session):
    """Create AuthenticationService instance for testing."""
    return AuthenticationService(db_session)

def test_register_user(auth_service):
    """Test user registration."""
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPass123!",
        "full_name": "Test User"
    }
    user = auth_service.register_user(user_data)
    assert user.email == user_data["email"]
    assert user.username == user_data["username"]
    assert user.full_name == user_data["full_name"]
    assert user.is_active is True

def test_authenticate_user(auth_service):
    """Test user authentication."""
    # Register user
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPass123!",
        "full_name": "Test User"
    }
    auth_service.register_user(user_data)
    
    # Test valid authentication
    user = auth_service.authenticate_user(user_data["email"], user_data["password"])
    assert user.email == user_data["email"]
    
    # Test invalid password
    with pytest.raises(HTTPException) as exc_info:
        auth_service.authenticate_user(user_data["email"], "wrong_password")
    assert exc_info.value.status_code == 401
    
    # Test non-existent user
    with pytest.raises(HTTPException) as exc_info:
        auth_service.authenticate_user("nonexistent@example.com", "password")
    assert exc_info.value.status_code == 401

def test_create_session(auth_service):
    """Test session creation."""
    # Register user
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPass123!",
        "full_name": "Test User"
    }
    user = auth_service.register_user(user_data)
    
    # Create session
    device_info = {"browser": "Chrome", "os": "Windows"}
    ip_address = "127.0.0.1"
    
    session = auth_service.create_session(
        user_id=user.id,
        device_info=device_info,
        ip_address=ip_address
    )
    
    assert session.user_id == user.id
    assert session.device_info == device_info
    assert session.ip_address == ip_address
    assert session.is_active is True
    assert session.session_token is not None
    assert session.refresh_token is not None

def test_validate_session(auth_service):
    """Test session validation."""
    # Create user and session
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPass123!",
        "full_name": "Test User"
    }
    user = auth_service.register_user(user_data)
    session = auth_service.create_session(
        user_id=user.id,
        device_info={"browser": "Chrome"},
        ip_address="127.0.0.1"
    )
    
    # Test valid session
    assert auth_service.validate_session(session.session_token) is True
    
    # Test invalid session
    assert auth_service.validate_session("invalid_token") is False
    
    # Test expired session
    session.expires_at = datetime.utcnow() - timedelta(minutes=1)
    auth_service.db.commit()
    assert auth_service.validate_session(session.session_token) is False

def test_end_session(auth_service):
    """Test session termination."""
    # Create user and session
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPass123!",
        "full_name": "Test User"
    }
    user = auth_service.register_user(user_data)
    session = auth_service.create_session(
        user_id=user.id,
        device_info={"browser": "Chrome"},
        ip_address="127.0.0.1"
    )
    
    # End session
    auth_service.end_session(session.session_token)
    
    # Verify session is ended
    ended_session = auth_service.get_session(session.session_token)
    assert ended_session.is_active is False
    assert ended_session.ended_at is not None

def test_password_reset(auth_service):
    """Test password reset functionality."""
    # Register user
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPass123!",
        "full_name": "Test User"
    }
    user = auth_service.register_user(user_data)
    
    # Request password reset
    reset_token = auth_service.request_password_reset(user.email)
    assert reset_token is not None
    
    # Reset password
    new_password = "NewPass456!"
    auth_service.reset_password(reset_token, new_password)
    
    # Verify new password works
    user = auth_service.authenticate_user(user.email, new_password)
    assert user is not None
    
    # Verify old password doesn't work
    with pytest.raises(HTTPException) as exc_info:
        auth_service.authenticate_user(user.email, user_data["password"])
    assert exc_info.value.status_code == 401

def test_email_verification(auth_service):
    """Test email verification functionality."""
    # Register user
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPass123!",
        "full_name": "Test User"
    }
    user = auth_service.register_user(user_data)
    
    # Request verification
    token = auth_service.request_email_verification(user.email)
    assert token is not None
    
    # Verify email
    auth_service.verify_email(token)
    
    # Check user is verified
    user = auth_service.get_user_by_email(user.email)
    assert user.is_verified is True
