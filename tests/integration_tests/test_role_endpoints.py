"""Integration tests for role management endpoints."""
import pytest
from fastapi.testclient import TestClient

def test_create_role(client, admin_headers):
    """Test role creation endpoint."""
    response = client.post(
        "/api/roles",
        json={
            "name": "test_role",
            "description": "Test role description",
            "permissions": ["user:read", "task:read"]
        },
        headers=admin_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "test_role"
    assert len(data["permissions"]) == 2

def test_get_role(client, admin_headers):
    """Test getting a role endpoint."""
    # First create a role
    response = client.post(
        "/api/roles",
        json={
            "name": "get_role",
            "description": "Role to get",
            "permissions": ["user:read"]
        },
        headers=admin_headers
    )
    role_id = response.json()["id"]
    
    # Get the role
    response = client.get(f"/api/roles/{role_id}", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "get_role"

def test_update_role(client, admin_headers):
    """Test role update endpoint."""
    # First create a role
    response = client.post(
        "/api/roles",
        json={
            "name": "update_role",
            "description": "Role to update",
            "permissions": ["user:read"]
        },
        headers=admin_headers
    )
    role_id = response.json()["id"]
    
    # Update the role
    response = client.put(
        f"/api/roles/{role_id}",
        json={
            "name": "updated_role",
            "description": "Updated description",
            "permissions": ["user:read", "user:write"]
        },
        headers=admin_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "updated_role"
    assert len(data["permissions"]) == 2

def test_delete_role(client, admin_headers):
    """Test role deletion endpoint."""
    # First create a role
    response = client.post(
        "/api/roles",
        json={
            "name": "delete_role",
            "description": "Role to delete",
            "permissions": ["user:read"]
        },
        headers=admin_headers
    )
    role_id = response.json()["id"]
    
    # Delete the role
    response = client.delete(f"/api/roles/{role_id}", headers=admin_headers)
    assert response.status_code == 204
    
    # Try to get the deleted role
    response = client.get(f"/api/roles/{role_id}", headers=admin_headers)
    assert response.status_code == 404

def test_list_roles(client, admin_headers):
    """Test listing roles endpoint."""
    # Create multiple roles
    roles = ["role1", "role2", "role3"]
    for role_name in roles:
        client.post(
            "/api/roles",
            json={
                "name": role_name,
                "description": f"Test role {role_name}",
                "permissions": ["user:read"]
            },
            headers=admin_headers
        )
    
    # List roles
    response = client.get("/api/roles", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= len(roles)

def test_get_role_permissions(client, admin_headers):
    """Test getting role permissions endpoint."""
    # Create a role with permissions
    response = client.post(
        "/api/roles",
        json={
            "name": "perm_role",
            "description": "Role with permissions",
            "permissions": ["user:read", "task:read"]
        },
        headers=admin_headers
    )
    role_id = response.json()["id"]
    
    # Get role permissions
    response = client.get(f"/api/roles/{role_id}/permissions", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert "user:read" in [p["name"] for p in data]

def test_update_role_permissions(client, admin_headers):
    """Test updating role permissions endpoint."""
    # Create a role
    response = client.post(
        "/api/roles",
        json={
            "name": "update_perm_role",
            "description": "Role for permission update",
            "permissions": ["user:read"]
        },
        headers=admin_headers
    )
    role_id = response.json()["id"]
    
    # Update permissions
    response = client.put(
        f"/api/roles/{role_id}/permissions",
        json={"permissions": ["user:write", "task:read"]},
        headers=admin_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["permissions"]) == 2
    
    # Verify updated permissions
    response = client.get(f"/api/roles/{role_id}/permissions", headers=admin_headers)
    data = response.json()
    perm_names = [p["name"] for p in data]
    assert "user:write" in perm_names
    assert "task:read" in perm_names
