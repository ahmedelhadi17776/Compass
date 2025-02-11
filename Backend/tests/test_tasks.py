import pytest
from fastapi import status
from datetime import datetime, timedelta

def test_create_task(test_client, test_user_token):
    """Test creating a new task."""
    headers = {"Authorization": f"Bearer {test_user_token}"}
    task_data = {
        "title": "Test Task",
        "description": "This is a test task",
        "due_date": (datetime.utcnow() + timedelta(days=1)).isoformat()
    }
    response = test_client.post("/tasks/", json=task_data, headers=headers)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["title"] == task_data["title"]
    return data["id"]

def test_get_task(test_client, test_user_token):
    """Test getting a specific task."""
    # First create a task
    task_id = test_create_task(test_client, test_user_token)
    
    headers = {"Authorization": f"Bearer {test_user_token}"}
    response = test_client.get(f"/tasks/{task_id}", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "title" in data
    assert "description" in data

def test_list_tasks(test_client, test_user_token):
    """Test listing all tasks for a user."""
    # First create a task
    test_create_task(test_client, test_user_token)
    
    headers = {"Authorization": f"Bearer {test_user_token}"}
    response = test_client.get("/tasks/", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) > 0

def test_update_task(test_client, test_user_token):
    """Test updating a task."""
    # First create a task
    task_id = test_create_task(test_client, test_user_token)
    
    headers = {"Authorization": f"Bearer {test_user_token}"}
    update_data = {
        "title": "Updated Task",
        "description": "This task has been updated"
    }
    response = test_client.put(f"/tasks/{task_id}", json=update_data, headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["title"] == update_data["title"]
    assert data["description"] == update_data["description"]

def test_delete_task(test_client, test_user_token):
    """Test deleting a task."""
    # First create a task
    task_id = test_create_task(test_client, test_user_token)
    
    headers = {"Authorization": f"Bearer {test_user_token}"}
    response = test_client.delete(f"/tasks/{task_id}", headers=headers)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    
    # Verify task is deleted
    response = test_client.get(f"/tasks/{task_id}", headers=headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_task_not_found(test_client, test_user_token):
    """Test accessing a non-existent task."""
    headers = {"Authorization": f"Bearer {test_user_token}"}
    response = test_client.get("/tasks/999999", headers=headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_unauthorized_access(test_client):
    """Test accessing tasks without authentication."""
    response = test_client.get("/tasks/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_task_validation(test_client, test_user_token):
    """Test task validation."""
    headers = {"Authorization": f"Bearer {test_user_token}"}
    invalid_task = {
        "title": "",  # Empty title should be invalid
        "description": "Test task"
    }
    response = test_client.post("/tasks/", json=invalid_task, headers=headers)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
