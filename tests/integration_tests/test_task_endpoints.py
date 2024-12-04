"""Integration tests for task management endpoints."""
import pytest
from fastapi import status

from src.data.database.models import Task, TaskStatus, TaskPriority

def test_create_task(client, auth_headers, db_session):
    """Test task creation endpoint."""
    task_data = {
        "title": "Test Task",
        "description": "Test task description",
        "priority": "MEDIUM",
        "status": "TODO",
        "due_date": "2024-12-31T23:59:59"
    }
    
    response = client.post("/api/tasks/", json=task_data, headers=auth_headers)
    assert response.status_code == status.HTTP_201_CREATED
    
    data = response.json()
    assert data["title"] == task_data["title"]
    assert data["description"] == task_data["description"]
    assert data["priority"] == task_data["priority"]
    assert data["status"] == task_data["status"]

def test_get_tasks(client, auth_headers, db_session):
    """Test getting task list."""
    # Create test tasks
    task_data = [
        {"title": "Task 1", "priority": "LOW", "status": "TODO"},
        {"title": "Task 2", "priority": "HIGH", "status": "IN_PROGRESS"},
    ]
    
    for task in task_data:
        client.post("/api/tasks/", json=task, headers=auth_headers)
    
    response = client.get("/api/tasks/", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert len(data) >= 2  # At least our 2 test tasks
    assert any(task["title"] == "Task 1" for task in data)
    assert any(task["title"] == "Task 2" for task in data)

def test_update_task(client, auth_headers, db_session):
    """Test task update endpoint."""
    # Create a task
    task_data = {
        "title": "Original Task",
        "priority": "LOW",
        "status": "TODO"
    }
    create_response = client.post("/api/tasks/", json=task_data, headers=auth_headers)
    task_id = create_response.json()["id"]
    
    # Update the task
    update_data = {
        "title": "Updated Task",
        "priority": "HIGH",
        "status": "IN_PROGRESS"
    }
    response = client.put(f"/api/tasks/{task_id}", json=update_data, headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert data["title"] == update_data["title"]
    assert data["priority"] == update_data["priority"]
    assert data["status"] == update_data["status"]

def test_delete_task(client, auth_headers, db_session):
    """Test task deletion endpoint."""
    # Create a task
    task_data = {
        "title": "Task to Delete",
        "priority": "LOW",
        "status": "TODO"
    }
    create_response = client.post("/api/tasks/", json=task_data, headers=auth_headers)
    task_id = create_response.json()["id"]
    
    # Delete the task
    response = client.delete(f"/api/tasks/{task_id}", headers=auth_headers)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    
    # Verify task is deleted
    get_response = client.get(f"/api/tasks/{task_id}", headers=auth_headers)
    assert get_response.status_code == status.HTTP_404_NOT_FOUND

def test_task_status_validation(client, auth_headers):
    """Test task creation with invalid status."""
    task_data = {
        "title": "Invalid Task",
        "priority": "LOW",
        "status": "INVALID_STATUS"  # Invalid status
    }
    
    response = client.post("/api/tasks/", json=task_data, headers=auth_headers)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_task_priority_validation(client, auth_headers):
    """Test task creation with invalid priority."""
    task_data = {
        "title": "Invalid Task",
        "priority": "INVALID_PRIORITY",  # Invalid priority
        "status": "TODO"
    }
    
    response = client.post("/api/tasks/", json=task_data, headers=auth_headers)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
