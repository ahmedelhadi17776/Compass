import pytest
from fastapi import status
from Backend.services.authentication.auth_service import WeakPasswordError

def test_register_user(test_client, test_user):
    """Test user registration."""
    response = test_client.post("/auth/register", json=test_user)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_user(test_client, test_user):
    """Test user login."""
    # First register the user
    test_client.post("/auth/register", json=test_user)
    
    # Then try to login
    login_data = {
        "username": test_user["username"],
        "password": test_user["password"]
    }
    response = test_client.post("/auth/login", data=login_data)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_wrong_password(test_client, test_user):
    """Test login with wrong password."""
    # First register the user
    test_client.post("/auth/register", json=test_user)
    
    # Then try to login with wrong password
    login_data = {
        "username": test_user["username"],
        "password": "wrongpassword"
    }
    response = test_client.post("/auth/login", data=login_data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_register_duplicate_username(test_client, test_user):
    """Test registering with duplicate username."""
    # Register first user
    test_client.post("/auth/register", json=test_user)
    
    # Try to register same username again
    duplicate_user = test_user.copy()
    duplicate_user["email"] = "another@example.com"
    response = test_client.post("/auth/register", json=duplicate_user)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

def test_register_duplicate_email(test_client, test_user):
    """Test registering with duplicate email."""
    # Register first user
    test_client.post("/auth/register", json=test_user)
    
    # Try to register same email again
    duplicate_user = test_user.copy()
    duplicate_user["username"] = "another_user"
    response = test_client.post("/auth/register", json=duplicate_user)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

def test_get_current_user(test_client, test_user_token, test_user):
    """Test getting current user info."""
    headers = {"Authorization": f"Bearer {test_user_token}"}
    response = test_client.get("/auth/me", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["username"] == test_user["username"]
    assert data["email"] == test_user["email"]

def test_weak_password_registration(test_client):
    """Test registration with weak password."""
    weak_user = {
        "username": "weakuser",
        "email": "weak@example.com",
        "password": "weak",
        "full_name": "Weak User"
    }
    response = test_client.post("/auth/register", json=weak_user)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

def test_missing_auth_header(test_client):
    """Test accessing protected endpoint without auth header."""
    response = test_client.get("/auth/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_invalid_token_format(test_client):
    """Test using malformed token."""
    headers = {"Authorization": "Bearer invalid_token"}
    response = test_client.get("/auth/me", headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_refresh_token(test_client, test_user_token):
    """Test refreshing access token."""
    headers = {"Authorization": f"Bearer {test_user_token}"}
    response = test_client.post("/auth/refresh", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["access_token"] != test_user_token
