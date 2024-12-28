import pytest
from fastapi.testclient import TestClient
from src.application.main import app
from src.core.database import get_db
from src.data.database.base import Base
from src.data.database.models import User
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from src.core.config import settings

# Setup test database
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./test.db"
engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)



async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(scope="module")
async def prepare_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


def test_register_user(prepare_database):
    response = client.post(
        "/auth/register",
        json={
            "email": "testuser@example.com",
            "username": "testuser",
            "password": "strongpassword123",
            "full_name": "Test User"
        }
    )
    assert response.status_code == 201
    assert "access_token" in response.json()


def test_login_user(prepare_database):
    # First, register the user
    client.post(
        "/auth/register",
        json={
            "email": "testlogin@example.com",
            "username": "testlogin",
            "password": "strongpassword123",
            "full_name": "Test Login"
        }
    )
    # Then, attempt to log in
    response = client.post(
        "/auth/login",
        data={
            "username": "testlogin@example.com",
            "password": "strongpassword123"
        }
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
