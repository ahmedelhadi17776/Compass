"""Test configuration and fixtures."""
import os
import sys
import pytest
import pytest_asyncio
from typing import List
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy import select
from datetime import datetime, timedelta, timezone
import asyncio

# Import and apply test configuration before importing app
from tests.test_config import test_settings, mock_email_service

# Set test environment variables
for key, value in test_settings.items():
    os.environ[key] = str(value)

# Import email service module first
import src.services.notification_service.email_service

# Then mock it
sys.modules['src.services.notification_service.email_service'].email_service = mock_email_service

# Now import app and other modules
from src.core.config import settings
from src.data.database.base import Base
from src.main import app
from src.data.database.models import User, UserSession, Role
from src.core.security import get_password_hash
from src.services.authentication.auth_service import AuthService

# Create async engine for testing
test_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    echo=False,
)

# Create async session factory
async_session_factory = sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

@pytest_asyncio.fixture
async def async_session():
    """Create a fresh database session for each test."""
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    session = async_session_factory()
    try:
        yield session
    finally:
        await session.close()
        # Drop tables
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture(scope="function")
async def db_session(async_session):
    """Create a fresh database session for each test."""
    yield async_session

@pytest.fixture
def setup_greenlet():
    """Set up greenlet for each test."""
    loop = asyncio.get_event_loop()
    return loop

@pytest_asyncio.fixture
async def client(db_session):
    """Create an async test client."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides = {}
    app.dependency_overrides["get_db"] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest_asyncio.fixture
async def test_user(async_session: AsyncSession):
    """Create a test user."""
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNhyZiBUpj2qq",  # testpassword123
        full_name="Test User",
        is_active=True,
        is_verified=True,
        created_at=datetime.now(timezone.utc)
    )
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)
    return user

@pytest_asyncio.fixture
async def test_user_session(db_session: AsyncSession, test_user: User):
    """Create a test user session."""
    session = UserSession(
        user_id=test_user.id,
        session_token="test_session_token",
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        is_active=True
    )
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)
    return session

@pytest_asyncio.fixture
async def locked_test_user(db_session: AsyncSession):
    """Create a locked test user."""
    user = User(
        email="locked@example.com",
        username="lockeduser",
        hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNhyZiBUpj2qq",  # testpassword123
        full_name="Locked User",
        is_active=True,
        is_verified=True,
        failed_login_attempts=settings.MAX_LOGIN_ATTEMPTS,
        account_locked_until=datetime.now(timezone.utc) + timedelta(minutes=15),
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest_asyncio.fixture
async def auth_service(db_session):
    """Create an AuthService instance for testing."""
    return AuthService(db_session)

@pytest_asyncio.fixture
async def auth_headers(test_user, auth_service):
    """Create authentication headers with a valid token."""
    user = await test_user
    token = auth_service.create_access_token({"sub": str(user.id)})
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(autouse=True)
async def cleanup_db(db_session):
    """Clean up the database after each test."""
    yield
    async with db_session.begin():
        for table in reversed(Base.metadata.sorted_tables):
            await db_session.execute(table.delete())
    db_session.commit()

@pytest_asyncio.fixture
async def test_admin(client, db_session):
    """Create a test admin user and return the user data."""
    from src.data.database.models import User, Role
    from src.core.security import get_password_hash
    
    # Create admin role if it doesn't exist
    admin_role = db_session.query(Role).filter_by(name="admin").first()
    if not admin_role:
        admin_role = Role(name="admin", description="Administrator")
        db_session.add(admin_role)
    
    # Create admin user
    admin_user = User(
        username="admin",
        email="admin@example.com",
        hashed_password=get_password_hash("AdminPass123!"),
        full_name="Admin User",
        is_active=True,
        is_admin=True
    )
    admin_user.roles.append(admin_role)
    db_session.add(admin_user)
    await db_session.commit()
    
    return {
        "id": admin_user.id,
        "username": admin_user.username,
        "email": admin_user.email,
        "full_name": admin_user.full_name
    }
