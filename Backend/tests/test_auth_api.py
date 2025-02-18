import pytest
from fastapi import status
from httpx import AsyncClient
from Backend.app.schemas.auth import Token, UserCreate
from Backend.app.schemas.user import UserResponse
from Backend.app.schemas.session import SessionResponse
from Backend.data_layer.database.models.session import SessionStatus
from urllib.parse import urlencode


@pytest.mark.asyncio
async def test_register(client: AsyncClient):
    response = await client.post(
        "/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123",
            "first_name": "Test",
            "last_name": "User"
        }
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert "password" not in data


@pytest.mark.asyncio
async def test_login(client: AsyncClient):
    # Register a user first
    register_response = await client.post(
        "/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123",
            "first_name": "Test",
            "last_name": "User"
        }
    )
    assert register_response.status_code == status.HTTP_200_OK
    print("📝 Register response:", register_response.json())

    # Try to login with proper OAuth2 form data
    login_data = {
        "username": "testuser",
        "password": "testpass123",
        "grant_type": "password",
        "scope": "",
        "client_id": "",
        "client_secret": ""
    }
    print("🔑 Login data:", login_data)

    # Ensure we're using the correct content type and form encoding
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }

    response = await client.post(
        "/auth/login",
        data=login_data,  # Let httpx handle the form encoding
        headers=headers
    )

    print("🔐 Login response status:", response.status_code)
    print("🔐 Login response content:", response.content)

    assert response.status_code == 200, f"Login failed with status {response.status_code}: {response.content}"
    data = response.json()
    assert "access_token" in data, f"No access token in response: {data}"
    assert data["token_type"] == "bearer"

    # Verify session was created
    token = data["access_token"]
    session_response = await client.get(
        "/auth/sessions",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert session_response.status_code == 200
    sessions = session_response.json()
    assert len(sessions) > 0
    session = sessions[0]
    assert session["is_valid"] is True
    assert session["status"] == SessionStatus.ACTIVE.value
    assert isinstance(session["device_info"],
                      dict) or session["device_info"] is None


@pytest.mark.asyncio
async def test_me_endpoint(client: AsyncClient):
    # Register and login first
    await client.post(
        "/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123",
            "first_name": "Test",
            "last_name": "User"
        }
    )

    # Try to login with proper OAuth2 form data
    form_data = {
        "username": "testuser",
        "password": "testpass123",
        "grant_type": "password",
        "scope": "",
        "client_id": "",
        "client_secret": ""
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    login_response = await client.post(
        "/auth/login",
        data=form_data,
        headers=headers
    )
    assert login_response.status_code == 200, f"Login failed with status {login_response.status_code}: {login_response.content}"
    token = login_response.json()["access_token"]

    # Test /me endpoint
    response = await client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_logout(client: AsyncClient):
    # Register and login first
    await client.post(
        "/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123",
            "first_name": "Test",
            "last_name": "User"
        }
    )

    # Try to login with proper OAuth2 form data
    form_data = {
        "username": "testuser",
        "password": "testpass123",
        "grant_type": "password",
        "scope": "",
        "client_id": "",
        "client_secret": ""
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    login_response = await client.post(
        "/auth/login",
        data=form_data,
        headers=headers
    )
    assert login_response.status_code == 200, f"Login failed with status {login_response.status_code}: {login_response.content}"
    token = login_response.json()["access_token"]

    # Test logout
    response = await client.post(
        "/auth/logout",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200

    # Verify session is invalidated
    session_response = await client.get(
        "/auth/sessions",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert session_response.status_code == 401  # Should be unauthorized now


@pytest.mark.asyncio
async def test_get_user_sessions(client: AsyncClient):
    # Register and login first
    await client.post(
        "/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123",
            "first_name": "Test",
            "last_name": "User"
        }
    )

    # Try to login with proper OAuth2 form data
    form_data = {
        "username": "testuser",
        "password": "testpass123",
        "grant_type": "password",
        "scope": "",
        "client_id": "",
        "client_secret": ""
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    login_response = await client.post(
        "/auth/login",
        data=form_data,
        headers=headers
    )
    assert login_response.status_code == 200, f"Login failed with status {login_response.status_code}: {login_response.content}"
    token = login_response.json()["access_token"]

    response = await client.get(
        "/auth/sessions",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    sessions = response.json()
    assert isinstance(sessions, list)
    assert len(sessions) > 0

    # Verify session fields
    session = sessions[0]
    assert isinstance(session, dict)
    assert "id" in session
    assert "user_id" in session
    assert session["status"] == SessionStatus.ACTIVE.value
    assert isinstance(session["device_info"],
                      dict) or session["device_info"] is None
    assert "created_at" in session
    assert "expires_at" in session
    assert "last_activity" in session
