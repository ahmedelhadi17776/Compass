"""Integration tests for user management endpoints."""
import pytest
from fastapi import status

def test_create_user(client):
    """Test user creation endpoint."""
    user_data = {
        "email": "newuser@example.com",
        "password": "StrongPass123!",
        "first_name": "New",
        "last_name": "User"
    }
    
    response = client.post("/api/users/", json=user_data)
    assert response.status_code == status.HTTP_201_CREATED
    
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["first_name"] == user_data["first_name"]
    assert data["last_name"] == user_data["last_name"]
    assert "password" not in data  # Password should not be in response

def test_get_users(client, admin_headers):
    """Test getting user list (admin only)."""
    response = client.get("/api/users/", headers=admin_headers)
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0  # Should at least have admin and test user

def test_get_user_by_id(client, test_user, auth_headers):
    """Test getting user by ID."""
    user_id = test_user["id"]
    response = client.get(f"/api/users/{user_id}", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert data["id"] == user_id
    assert data["email"] == test_user["email"]

def test_update_user(client, test_user, auth_headers):
    """Test user update endpoint."""
    user_id = test_user["id"]
    update_data = {
        "first_name": "Updated",
        "last_name": "Name"
    }
    
    response = client.put(f"/api/users/{user_id}", json=update_data, headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert data["first_name"] == update_data["first_name"]
    assert data["last_name"] == update_data["last_name"]

def test_delete_user(client, admin_headers):
    """Test user deletion (admin only)."""
    # Create a user to delete
    user_data = {
        "email": "todelete@example.com",
        "password": "DeleteMe123!",
        "first_name": "Delete",
        "last_name": "User"
    }
    create_response = client.post("/api/users/", json=user_data)
    user_id = create_response.json()["id"]
    
    # Delete the user
    response = client.delete(f"/api/users/{user_id}", headers=admin_headers)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    
    # Verify user is deleted
    get_response = client.get(f"/api/users/{user_id}", headers=admin_headers)
    assert get_response.status_code == status.HTTP_404_NOT_FOUND

def test_unauthorized_access(client, auth_headers):
    """Test unauthorized access to admin-only endpoints."""
    # Try to access user list without admin rights
    response = client.get("/api/users/", headers=auth_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN

def test_invalid_email_format(client):
    """Test user creation with invalid email format."""
    user_data = {
        "email": "invalid-email",
        "password": "StrongPass123!",
        "first_name": "Test",
        "last_name": "User"
    }
    
    response = client.post("/api/users/", json=user_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_weak_password(client):
    """Test user creation with weak password."""
    user_data = {
        "email": "test@example.com",
        "password": "weak",  # Too short and simple
        "first_name": "Test",
        "last_name": "User"
    }
    
    response = client.post("/api/users/", json=user_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
