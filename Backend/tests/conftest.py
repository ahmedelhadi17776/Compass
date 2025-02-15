import asyncio
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from data_layer.database.models.base import Base
from data_layer.database.session import get_db
from main import app
import os
import pathlib

# Set testing environment before importing settings
os.environ["TESTING"] = "True"
os.environ["APP_NAME"] = "COMPASS_TEST"
os.environ["APP_VERSION"] = "test"
os.environ["ENVIRONMENT"] = "testing"
os.environ["JWT_SECRET_KEY"] = "test_secret_key"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"

# Use in-memory SQLite for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="function")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def engine():
    """Create engine instance for each test."""
    test_engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True,
        pool_pre_ping=True
    )

    try:
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
    except SQLAlchemyError as e:
        await test_engine.dispose()
        raise pytest.fail(f"Failed to setup database: {str(e)}")

    yield test_engine

    try:
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    except SQLAlchemyError as e:
        print(f"Warning: Failed to cleanup database: {str(e)}")
    finally:
        await test_engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(engine):
    """Get a TestingSession instance."""
    TestingSessionLocal = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False
    )

    async with TestingSessionLocal() as session:
        try:
            yield session
            await session.rollback()
        except SQLAlchemyError as e:
            await session.rollback()
            raise pytest.fail(f"Database session error: {str(e)}")
        finally:
            await session.close()


@pytest_asyncio.fixture(scope="function")
async def client(db_session):
    """Get a TestClient instance with overridden dependencies."""
    async def override_get_db():
        try:
            yield db_session
        finally:
            await db_session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
