import pytest
from fastapi.testclient import TestClient
from app.schemas.auth import Token, UserCreate
from app.schemas.user import UserResponse
from app.schemas.session import SessionResponse
from data_layer.database.models.session import SessionStatus


def test_register(client: TestClient):
    response = client.post(
        "/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123",
            "first_name": "Test",
            "last_name": "User"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert "password" not in data


def test_login(client: TestClient):
    # Register a user first
    client.post(
        "/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123"
        }
    )

    # Try to login
    response = client.post(
        "/auth/login",
        data={
            "username": "testuser",
            "password": "testpass123"
        },
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    # Verify session was created
    token = data["access_token"]
    session_response = client.get(
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


def test_me_endpoint(client: TestClient):
    # Register and login first
    client.post(
        "/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123"
        }
    )

    login_response = client.post(
        "/auth/login",
        data={
            "username": "testuser",
            "password": "testpass123"
        }
    )
    token = login_response.json()["access_token"]

    # Test /me endpoint
    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"


def test_logout(client: TestClient):
    # Register and login first
    client.post(
        "/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123"
        }
    )

    login_response = client.post(
        "/auth/login",
        data={
            "username": "testuser",
            "password": "testpass123"
        }
    )
    token = login_response.json()["access_token"]

    # Test logout
    response = client.post(
        "/auth/logout",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200

    # Verify session is invalidated
    session_response = client.get(
        "/auth/sessions",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert session_response.status_code == 401  # Should be unauthorized now


def test_get_user_sessions(client: TestClient):
    # Register and login first
    client.post(
        "/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123"
        }
    )

    login_response = client.post(
        "/auth/login",
        data={
            "username": "testuser",
            "password": "testpass123"
        },
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
    )
    token = login_response.json()["access_token"]

    response = client.get(
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
