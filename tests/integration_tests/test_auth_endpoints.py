"""Integration tests for authentication endpoints."""
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from src.core.config import settings

def test_register_user(client):
    """Test user registration endpoint."""
    user_data = {
        "email": "test@example.com",
        "password": "Test@123",
        "full_name": "Test User"
    }
    response = client.post("/api/auth/register", json=user_data)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"

def test_login_user(client, test_user):
    """Test user login endpoint."""
    login_data = {
        "email": test_user["email"],
        "password": test_user["password"]
    }
    response = client.post("/api/auth/login", data=login_data)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"

def test_invalid_login(client):
    """Test login with invalid credentials."""
    login_data = {
        "email": "wrong@email.com",
        "password": "wrongpass"
    }
    response = client.post("/api/auth/login", data=login_data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_get_current_user(client, auth_headers):
    """Test getting current user info."""
    response = client.get("/api/auth/me", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "email" in data
    assert "full_name" in data
    assert "is_verified" in data

def test_refresh_token(client, auth_headers):
    """Test token refresh endpoint."""
    response = client.post("/api/auth/refresh", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data

def test_logout(client, auth_headers):
    """Test logout endpoint."""
    response = client.post("/api/auth/logout", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK

def test_password_reset_request(client, test_user):
    """Test password reset request endpoint."""
    data = {"email": test_user["email"]}
    response = client.post("/api/auth/password-reset/request", json=data)
    assert response.status_code == status.HTTP_200_OK

def test_password_reset_confirm(client, test_user):
    """Test password reset confirmation endpoint."""
    # First request reset token
    response = client.post("/api/auth/password-reset/request", 
                          json={"email": test_user["email"]})
    assert response.status_code == status.HTTP_200_OK

    # Get reset token from response
    reset_token = response.json()["reset_token"]
    
    # Confirm password reset
    new_password = "NewTest@123"
    response = client.post(
        "/api/auth/password-reset/confirm",
        json={
            "token": reset_token,
            "new_password": new_password
        }
    )
    assert response.status_code == status.HTTP_200_OK

    # Try logging in with new password
    login_data = {
        "email": test_user["email"],
        "password": new_password
    }
    response = client.post("/api/auth/login", data=login_data)
    assert response.status_code == status.HTTP_200_OK
