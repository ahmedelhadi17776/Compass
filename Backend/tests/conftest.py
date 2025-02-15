import asyncio
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from Backend.data_layer.database.models.base import Base
from Backend.data_layer.database.models import User, Organization
from Backend.data_layer.database.session import get_db as get_async_session
from Backend.main import app
import os
import pathlib
from typing import AsyncGenerator, Generator, AsyncIterator
import asyncpg
from sqlalchemy.pool import NullPool
from Backend.core.config import settings
import datetime
from redis.asyncio import Redis
from httpx import AsyncClient
import redis.asyncio as redis

# Set testing environment before importing settings
os.environ["TESTING"] = "True"
os.environ["APP_NAME"] = "COMPASS_TEST"
os.environ["APP_VERSION"] = "test"
os.environ["ENVIRONMENT"] = "testing"
os.environ["JWT_SECRET_KEY"] = "test_secret_key"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"

# Create test database engine
test_engine = create_async_engine(
    settings.TEST_DATABASE_URL,
    poolclass=NullPool,
    echo=True,
    isolation_level='AUTOCOMMIT'  # This is important for test setup
)

TestingSessionLocal = sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


@pytest_asyncio.fixture(autouse=True)
async def celery_config() -> None:
    """Configure Celery for testing."""
    from Backend.core.celery_app import celery_app

    # Configure Celery for testing
    test_config = {
        "task_always_eager": True,
        "task_eager_propagates": True,
        "broker_url": "memory://",
        "result_backend": "redis://localhost:6379/1",
        "broker_connection_retry": False,
        "broker_connection_retry_on_startup": False,
        "worker_cancel_long_running_tasks_on_connection_loss": True,
        "task_serializer": "json",
        "result_serializer": "json",
        "accept_content": ["json"],
        "task_track_started": True,
        "task_time_limit": 30,
        "task_soft_time_limit": 20,
        "worker_max_tasks_per_child": 1,
        "worker_max_memory_per_child": 50000,
        "task_store_errors_even_if_ignored": True
    }

    celery_app.conf.update(test_config)

    # Update settings for testing
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.CELERY_BROKER_URL = "memory://"
    settings.CELERY_RESULT_BACKEND = "redis://localhost:6379/1"
    settings.CELERY_TASK_EAGER_PROPAGATES = True


async def create_test_database():
    """Create test database if it doesn't exist."""
    try:
        # Connect to default database to create test database
        conn = await asyncpg.connect(
            user='postgres',
            password='0502747598',
            database='postgres',
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


@pytest_asyncio.fixture(scope="function")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_engine():
    """Create tables before tests and drop them after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield test_engine

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Get a TestingSessionLocal instance that manages transactions properly."""
    connection = await db_engine.connect()
    transaction = await connection.begin()

    session = TestingSessionLocal(bind=connection)

    try:
        yield session
    finally:
        await session.close()
        await transaction.rollback()
        await connection.close()


@pytest_asyncio.fixture
async def redis_client() -> AsyncGenerator[Redis, None]:
    """Get a Redis client instance."""
    client = redis.from_url(
        settings.TEST_REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
        socket_connect_timeout=1,
        socket_timeout=1,
        retry_on_timeout=True
    )
    try:
        await client.ping()  # Test connection
        await client.flushdb()  # Clear test database
        yield client
    except redis.ConnectionError:
        pytest.skip("Redis server not available")
    finally:
        try:
            await client.flushdb()
            await client.close()
        except:
            pass


@pytest.fixture
async def client(db_session: AsyncSession, redis_client: Redis) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client with the test database session and Redis client."""
    # Store original dependencies
    original_deps = app.dependency_overrides.copy()

    async def get_test_session():
        return db_session

    try:
        # Set up test dependencies
        app.dependency_overrides[get_async_session] = get_test_session
        app.state.redis = redis_client

        async with AsyncClient(
            app=app,
            base_url="http://test",
            follow_redirects=True
        ) as test_client:
            yield test_client
    finally:
        # Restore original dependencies
        app.dependency_overrides = original_deps
        app.state.redis = None
