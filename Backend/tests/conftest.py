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
    isolation_level='READ COMMITTED'  # Changed from AUTOCOMMIT
)

TestingSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
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
            password='1357997531',
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


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_database():
    """Create tables before each test and drop them after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


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
