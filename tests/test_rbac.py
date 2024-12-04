import pytest
from fastapi import status

def test_create_permission(test_client, test_user_token):
    """Test creating a new permission."""
    headers = {"Authorization": f"Bearer {test_user_token}"}
    permission_data = {
        "name": "create_task",
        "description": "Allows creating new tasks",
        "resource": "tasks",
        "action": "create"
    }
    response = test_client.post("/permissions/", json=permission_data, headers=headers)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == permission_data["name"]
    assert data["resource"] == permission_data["resource"]
    return data["id"]

def test_create_role(test_client, test_user_token):
    """Test creating a new role."""
    # First create a permission
    permission_id = test_create_permission(test_client, test_user_token)
    
    headers = {"Authorization": f"Bearer {test_user_token}"}
    role_data = {
        "name": "task_manager",
        "description": "Can manage tasks",
        "permissions": [permission_id]
    }
    response = test_client.post("/roles/", json=role_data, headers=headers)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == role_data["name"]
    return data["id"]

def test_assign_role_to_user(test_client, test_user_token):
    """Test assigning a role to a user."""
    # First create a role
    role_id = test_create_role(test_client, test_user_token)
    
    headers = {"Authorization": f"Bearer {test_user_token}"}
    update_data = {
        "role_id": role_id
    }
    response = test_client.put("/users/me", json=update_data, headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["role_id"] == role_id

def test_permission_check(test_client, test_user_token):
    """Test permission checking."""
    # First create and assign role with permission
    role_id = test_create_role(test_client, test_user_token)
    headers = {"Authorization": f"Bearer {test_user_token}"}
    
    # Update user's role
    test_client.put("/users/me", json={"role_id": role_id}, headers=headers)
    
    # Try to create a task (should succeed with proper permission)
    task_data = {
        "title": "Test Task",
        "description": "Testing permissions",
        "due_date": "2024-03-01T00:00:00Z"
    }
    response = test_client.post("/tasks/", json=task_data, headers=headers)
    assert response.status_code == status.HTTP_201_CREATED

def test_permission_denied(test_client, test_user_token):
    """Test permission denial."""
    headers = {"Authorization": f"Bearer {test_user_token}"}
    
    # Try to create a permission without proper role
    permission_data = {
        "name": "test_permission",
        "description": "Test permission",
        "resource": "test",
        "action": "test"
    }
    response = test_client.post("/permissions/", json=permission_data, headers=headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN

def test_list_permissions(test_client, test_user_token):
    """Test listing permissions."""
    # First create a permission
    test_create_permission(test_client, test_user_token)
    
    headers = {"Authorization": f"Bearer {test_user_token}"}
    response = test_client.get("/permissions/", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) > 0

def test_list_roles(test_client, test_user_token):
    """Test listing roles."""
    # First create a role
    test_create_role(test_client, test_user_token)
    
    headers = {"Authorization": f"Bearer {test_user_token}"}
    response = test_client.get("/roles/", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) > 0
