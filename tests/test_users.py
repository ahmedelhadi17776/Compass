import pytest
from fastapi import status

def test_get_current_user(test_client, test_user, test_user_token):
    """Test getting current user information."""
    headers = {"Authorization": f"Bearer {test_user_token}"}
    response = test_client.get("/users/me", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["username"] == test_user["username"]
    assert data["email"] == test_user["email"]

def test_update_user(test_client, test_user, test_user_token):
    """Test updating user information."""
    headers = {"Authorization": f"Bearer {test_user_token}"}
    update_data = {
        "first_name": "Updated",
        "last_name": "Name"
    }
    response = test_client.put("/users/me", headers=headers, json=update_data)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["first_name"] == update_data["first_name"]
    assert data["last_name"] == update_data["last_name"]

def test_change_password(test_client, test_user, test_user_token):
    """Test changing user password."""
    headers = {"Authorization": f"Bearer {test_user_token}"}
    password_data = {
        "current_password": test_user["password"],
        "new_password": "newpassword123"
    }
    response = test_client.post("/users/me/change-password", headers=headers, json=password_data)
    assert response.status_code == status.HTTP_200_OK
    assert "success" in response.json()["message"].lower()
    
    # Try logging in with new password
    login_data = {
        "username": test_user["username"],
        "password": password_data["new_password"]
    }
    response = test_client.post("/auth/login", json=login_data)
    assert response.status_code == status.HTTP_200_OK

def test_change_password_wrong_current(test_client, test_user, test_user_token):
    """Test changing password with wrong current password."""
    headers = {"Authorization": f"Bearer {test_user_token}"}
    password_data = {
        "current_password": "wrongpassword",
        "new_password": "newpassword123"
    }
    response = test_client.post("/users/me/change-password", headers=headers, json=password_data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "incorrect password" in response.json()["detail"].lower()

def test_list_users(test_client, test_user, test_user_token):
    """Test listing users."""
    headers = {"Authorization": f"Bearer {test_user_token}"}
    response = test_client.get("/users/", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "users" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert len(data["users"]) > 0
    assert data["users"][0]["username"] == test_user["username"]

def test_get_user_by_id(test_client, test_user, test_user_token):
    """Test getting user by ID."""
    # First get the user's ID
    headers = {"Authorization": f"Bearer {test_user_token}"}
    me_response = test_client.get("/users/me", headers=headers)
    user_id = me_response.json()["user_id"]
    
    # Then get user by ID
    response = test_client.get(f"/users/{user_id}", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["username"] == test_user["username"]
    assert data["email"] == test_user["email"]

def test_get_nonexistent_user(test_client, test_user_token):
    """Test getting non-existent user."""
    headers = {"Authorization": f"Bearer {test_user_token}"}
    response = test_client.get("/users/999", headers=headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in response.json()["detail"].lower()

def test_delete_user(test_client, test_user, test_user_token):
    """Test deleting a user."""
    # Create another user to delete
    new_user = {
        "username": "todelete",
        "email": "delete@example.com",
        "password": "password123"
    }
    register_response = test_client.post("/auth/register", json=new_user)
    new_user_id = register_response.json()["user_id"]
    
    # Delete the new user
    headers = {"Authorization": f"Bearer {test_user_token}"}
    response = test_client.delete(f"/users/{new_user_id}", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert "deleted successfully" in response.json()["message"].lower()
    
    # Try to get deleted user
    response = test_client.get(f"/users/{new_user_id}", headers=headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
