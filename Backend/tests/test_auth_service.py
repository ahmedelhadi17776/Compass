import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from fastapi import HTTPException
from services.auth_service import AuthService
from data_layer.repositories.user_repository import UserRepository
from data_layer.repositories.session_repository import SessionRepository
from app.schemas.auth import UserCreate
from data_layer.database.models.session import SessionStatus
from utils.security_utils import create_access_token

pytestmark = pytest.mark.asyncio  # Mark all tests as async


@pytest_asyncio.fixture
async def auth_service(db_session):
    """Get AuthService instance."""
    user_repo = UserRepository(db_session)
    session_repo = SessionRepository(db_session)
    service = AuthService(user_repo, session_repo)
    return service


@pytest_asyncio.fixture
async def test_user(auth_service):
    """Create a test user."""
    user_data = UserCreate(
        username="testuser",
        email="test@example.com",
        password="testpass123",
        first_name="Test",
        last_name="User"
    )
    return await auth_service.register_user(user_data)


async def test_register_user(auth_service):
    user_data = UserCreate(
        username="newuser",
        email="new@example.com",
        password="pass123",
        first_name="New",
        last_name="User"
    )

    user = await auth_service.register_user(user_data)
    assert user.username == "newuser"
    assert user.email == "new@example.com"
    assert user.first_name == "New"
    assert user.last_name == "User"
    assert user.is_active is True
    assert user.is_superuser is False


async def test_register_duplicate_username(auth_service, test_user):
    user_data = UserCreate(
        username="testuser",  # Same username as test_user
        email="another@example.com",
        password="pass123"
    )

    with pytest.raises(HTTPException) as exc_info:
        await auth_service.register_user(user_data)
    assert exc_info.value.status_code == 400
    assert "Username already registered" in str(exc_info.value.detail)


async def test_authenticate_user_success(auth_service, test_user):
    user = await auth_service.authenticate_user("testuser", "testpass123")
    assert user is not None
    assert user.username == "testuser"
    assert user.email == "test@example.com"


async def test_authenticate_user_wrong_password(auth_service, test_user):
    user = await auth_service.authenticate_user("testuser", "wrongpass")
    assert user is False


async def test_authenticate_user_nonexistent(auth_service):
    user = await auth_service.authenticate_user("nonexistent", "pass123")
    assert user is False


async def test_create_access_token():
    token_data = {"sub": "testuser"}
    expires_delta = timedelta(minutes=15)

    token = create_access_token(token_data, expires_delta)
    assert isinstance(token, str)
    assert len(token) > 0


async def test_create_session(auth_service, test_user):
    device_info = "Test Browser"
    ip_address = "127.0.0.1"

    session = await auth_service.create_session(
        user_id=test_user.id,
        device_info=device_info,
        ip_address=ip_address
    )

    assert session.user_id == test_user.id
    assert session.device_info == {"user_agent": device_info}
    assert session.ip_address == ip_address
    assert session.is_valid is True
    assert session.status == SessionStatus.ACTIVE
    assert isinstance(session.expires_at, datetime)
    assert session.token is not None
    assert len(session.token) > 0


async def test_validate_session(auth_service, test_user):
    session = await auth_service.create_session(
        user_id=test_user.id,
        device_info="Test Browser",
        ip_address="127.0.0.1"
    )

    valid_session = await auth_service.validate_session(session.token)
    assert valid_session.id == session.id
    assert valid_session.is_valid is True
    assert valid_session.status == SessionStatus.ACTIVE


async def test_validate_invalid_session(auth_service, test_user):
    session = await auth_service.create_session(
        user_id=test_user.id,
        device_info="Test Browser",
        ip_address="127.0.0.1"
    )

    # Invalidate the session
    await auth_service.invalidate_session(session.token)

    with pytest.raises(HTTPException) as exc_info:
        await auth_service.validate_session(session.token)
    assert exc_info.value.status_code == 401


async def test_get_user_sessions(auth_service, test_user):
    # Create multiple sessions
    session1 = await auth_service.create_session(test_user.id, "Browser 1", "127.0.0.1")
    session2 = await auth_service.create_session(test_user.id, "Browser 2", "127.0.0.2")

    sessions = await auth_service.get_user_sessions(test_user.id)
    assert len(sessions) == 2
    assert all(session.user_id == test_user.id for session in sessions)
    assert all(session.is_valid for session in sessions)
    assert all(session.status == SessionStatus.ACTIVE for session in sessions)

    # Verify session details
    assert any(s.device_info == {"user_agent": "Browser 1"} for s in sessions)
    assert any(s.device_info == {"user_agent": "Browser 2"} for s in sessions)
    assert any(s.ip_address == "127.0.0.1" for s in sessions)
    assert any(s.ip_address == "127.0.0.2" for s in sessions)


async def test_invalidate_session(auth_service, test_user):
    session = await auth_service.create_session(
        user_id=test_user.id,
        device_info="Test Browser",
        ip_address="127.0.0.1"
    )

    result = await auth_service.invalidate_session(session.token)
    assert result is True

    # Verify session is invalid
    with pytest.raises(HTTPException):
        await auth_service.validate_session(session.token)

    # Get session and verify status
    sessions = await auth_service.get_user_sessions(test_user.id)
    assert len(sessions) == 0  # Should not return invalid sessions
