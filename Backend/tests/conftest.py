from Backend.api.daily_habits_routes import router as daily_habits_router
from fastapi import FastAPI
from Backend.data_layer.database.models.daily_habits import DailyHabit
from Backend.data_layer.database.connection import get_test_db
import asyncio
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from Backend.data_layer.database.models.base import Base
from Backend.data_layer.database.models import User, Organization
from Backend.data_layer.database.connection import get_db as get_async_session
from Backend.main import app
import os
import pathlib
from typing import AsyncGenerator, Generator, AsyncIterator, Optional
import asyncpg
from sqlalchemy.pool import NullPool
from Backend.core.config import settings
import datetime
from redis.asyncio import Redis
from httpx import AsyncClient
import redis.asyncio as redis
import sys
from unittest.mock import MagicMock, patch
from sqlalchemy import text

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))

# Set testing environment before importing settings
os.environ["TESTING"] = "1"
os.environ["APP_NAME"] = "COMPASS_TEST"
os.environ["APP_VERSION"] = "test"
os.environ["ENVIRONMENT"] = "testing"
os.environ["JWT_SECRET_KEY"] = "test_secret_key"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"
os.environ["REDIS_URL"] = "redis://localhost:6379/1"

# Create test database engine
test_engine = create_async_engine(
    settings.TEST_DATABASE_URL,
    poolclass=NullPool,
    echo=True,
    isolation_level='READ COMMITTED'  # Changed from AUTOCOMMIT
)

TestingSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

# Import after setting environment variables

# Create a minimal version of the app for testing
test_app = FastAPI()

# Add only the routes we need for testing
test_app.include_router(daily_habits_router,
                        prefix="/daily-habits", tags=["daily-habits"])

# Mock Redis for testing


class MockRedis:
    def __init__(self):
        self.data = {}

    async def get(self, key):
        return self.data.get(key)

    async def set(self, key, value, ex=None):
        self.data[key] = value

    async def delete(self, key):
        if key in self.data:
            del self.data[key]

    async def close(self):
        pass

# Add Redis to app state


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def redis_client():
    redis = MockRedis()
    yield redis


@pytest.fixture
async def app_with_redis(redis_client):
    test_app.state.redis = redis_client
    yield test_app


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get a test database session."""
    async for session in get_test_db():
        yield session


@pytest.fixture
async def client(app_with_redis) -> AsyncGenerator[AsyncClient, None]:
    """Get a test client for the FastAPI app."""
    async with AsyncClient(app=app_with_redis, base_url="http://test") as client:
        yield client


@pytest.fixture
async def test_habit(db_session):
    """Create a test habit for testing."""
    from datetime import date, timedelta

    habit = DailyHabit(
        user_id=1,
        habit_name="Test Habit",
        description="A test habit for testing",
        start_day=date.today() - timedelta(days=7),
        end_day=date.today() + timedelta(days=30),
        current_streak=0,
        longest_streak=0,
        is_completed=False
    )
    db_session.add(habit)
    await db_session.flush()
    await db_session.commit()

    # Refresh to get the ID
    await db_session.refresh(habit)

    yield habit

    # Cleanup
    await db_session.delete(habit)
    await db_session.commit()


@pytest_asyncio.fixture(autouse=True)
async def celery_config() -> None:
    """Configure Celery for testing."""
    # Skip celery configuration for tests that don't need it
    # This avoids the import error with Backend.core.celery_app

    # Just set the testing flags without importing celery
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.CELERY_BROKER_URL = "memory://"
    settings.CELERY_RESULT_BACKEND = "redis://localhost:6379/1"
    settings.CELERY_TASK_EAGER_PROPAGATES = True

    yield


async def create_test_database():
    """Create test database if it doesn't exist."""
    try:
        # Connect to default database to create test database
        conn = await asyncpg.connect(
            user='postgres',
            password='0502747598',
            database='compass_test',
            host='localhost',
            port=5432
        )

        # Check if database exists
        exists = await conn.fetchval(
            'SELECT 1 FROM pg_database WHERE datname = $1',
            'compass_test'
        )

        if not exists:
            # Create test database
            await conn.execute('CREATE DATABASE compass_test')
            print("Created test database 'compass_test'")

        await conn.close()

    except Exception as e:
        print(f"Error creating test database: {e}")
        raise


@pytest_asyncio.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_database():
    """Create tables before each test and drop them after."""
    async with test_engine.begin() as conn:
        # Drop tables first
        await conn.run_sync(Base.metadata.drop_all)

        # Drop enum types
        await conn.execute(text("DROP TYPE IF EXISTS projectstatus"))
        await conn.execute(text("DROP TYPE IF EXISTS taskstatus"))
        await conn.execute(text("DROP TYPE IF EXISTS workflowstatus"))

        # Create enum types
        await conn.execute(text("""
            CREATE TYPE projectstatus AS ENUM (
                'ACTIVE', 'COMPLETED', 'ARCHIVED', 'ON_HOLD'
            )
        """))
        await conn.execute(text("""
            CREATE TYPE taskstatus AS ENUM (
                'TODO', 'IN_PROGRESS', 'COMPLETED', 'BLOCKED'
            )
        """))
        await conn.execute(text("""
            CREATE TYPE workflowstatus AS ENUM (
                'ACTIVE', 'COMPLETED', 'FAILED', 'PENDING'
            )
        """))

        # Create tables
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.execute(text("DROP TYPE IF EXISTS projectstatus"))
        await conn.execute(text("DROP TYPE IF EXISTS taskstatus"))
        await conn.execute(text("DROP TYPE IF EXISTS workflowstatus"))


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get a test database session."""
    async with TestingSessionLocal() as session:
        try:
            # Start a transaction
            await session.begin()

            # Return the session for the test to use
            yield session

            # After the test, commit any pending changes
            await session.commit()
        except Exception as e:
            # If there was an error, rollback
            if session.in_transaction():
                await session.rollback()
            raise e
        finally:
            # Always close the session
            await session.close()


@pytest_asyncio.fixture
async def redis_client() -> AsyncGenerator[Optional[Redis], None]:
    """Get a Redis client instance. Returns None if Redis is not available."""
    client = None
    try:
        client = redis.from_url(
            settings.TEST_REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=1,
            socket_timeout=1,
            retry_on_timeout=False,
            retry_on_error=None
        )
        await client.ping()
        await client.flushdb()
        yield client
    except (redis.ConnectionError, redis.TimeoutError) as e:
        print(f"Redis connection failed: {e}")
        yield None
    finally:
        if client:
            try:
                await client.flushdb()
                await client.aclose()
            except Exception as e:
                print(f"Error closing Redis client: {e}")


@pytest_asyncio.fixture
async def client(db_session: AsyncSession, redis_client: Redis) -> AsyncGenerator[AsyncClient, None]:
    """Get a test client."""
    async def override_get_db():
        try:
            yield db_session
        except Exception:
            await db_session.rollback()
            raise

    app.dependency_overrides[get_async_session] = override_get_db
    app.state.redis = redis_client

    async with AsyncClient(app=app, base_url="http://test") as ac:
        try:
            yield ac
        finally:
            app.dependency_overrides.clear()
            app.state.redis = None


@pytest.fixture(scope="session", autouse=True)
def mock_chroma_client():
    """Mock ChromaDB client to prevent actual initialization during tests."""
    # Create a mock collection with all the methods we need
    mock_collection = MagicMock()
    mock_collection.query.return_value = {
        "documents": [["This is a test document"]],
        "metadatas": [[{"source": "test", "date": "2023-01-01"}]],
        "distances": [[0.1]],
        "ids": [["test-id-1"]]
    }
    mock_collection.add.return_value = None
    mock_collection.update.return_value = None
    mock_collection.delete.return_value = None
    mock_collection.count.return_value = 1

    # Create a mock client that returns our mock collection
    mock_client = MagicMock()
    mock_client.get_or_create_collection.return_value = mock_collection

    # Create a mock ChromaClient class
    mock_chroma_client = MagicMock()
    mock_chroma_client.client = mock_client
    mock_chroma_client.collection = mock_collection

    # Patch the ChromaClient class and its initialization
    with patch('Backend.data_layer.vector_db.chroma_client.ChromaClient', return_value=mock_chroma_client):
        with patch('Backend.data_layer.vector_db.chroma_client.chromadb.PersistentClient', return_value=mock_client):
            with patch('Backend.ai_services.rag.rag_service.ChromaClient', return_value=mock_chroma_client):
                yield mock_chroma_client
