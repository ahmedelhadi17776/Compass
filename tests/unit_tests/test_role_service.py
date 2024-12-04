"""Unit tests for role service."""
import pytest
from datetime import datetime

from src.services.authorization.role_service import RoleService
from src.application.schemas.role import RoleCreate, RoleUpdate
from src.data.database.models import Role, Permission

def test_create_role(db_session):
    """Test role creation."""
    role_service = RoleService(db_session)
    
    # Create test permissions first
    permission1 = Permission(
        name="user:read",
        description="Read user data",
        resource="user",
        action="read",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    permission2 = Permission(
        name="task:read",
        description="Read task data",
        resource="task",
        action="read",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add_all([permission1, permission2])
    db_session.commit()
    
    role_data = RoleCreate(
        name="test_role",
        description="Test role description",
        permissions=[permission1.id, permission2.id]
    )
    
    role = role_service.create_role(role_data)
    assert role is not None
    assert role.name == role_data.name
    assert role.description == role_data.description
    
    # Check permissions
    permissions = [p.id for p in role.permissions]
    assert permission1.id in permissions
    assert permission2.id in permissions

def test_get_role(db_session):
    """Test getting a role."""
    role_service = RoleService(db_session)
    
    # Create test role
    role_data = RoleCreate(
        name="get_role_test",
        description="Test role for get operation",
        permissions=[]
    )
    created_role = role_service.create_role(role_data)
    
    # Get role by ID
    role = role_service.get_role(created_role.id)
    assert role is not None
    assert role.name == role_data.name
    
    # Get role by name
    role = role_service.get_role_by_name(role_data.name)
    assert role is not None
    assert role.id == created_role.id

def test_update_role(db_session):
    """Test role update."""
    role_service = RoleService(db_session)
    
    # Create test role
    role_data = RoleCreate(
        name="update_role_test",
        description="Test role for update operation",
        permissions=[]
    )
    created_role = role_service.create_role(role_data)
    
    # Update role
    update_data = RoleUpdate(
        name="updated_role",
        description="Updated description"
    )
    updated_role = role_service.update_role(created_role.id, update_data)
    
    assert updated_role is not None
    assert updated_role.name == update_data.name
    assert updated_role.description == update_data.description

def test_delete_role(db_session):
    """Test role deletion."""
    role_service = RoleService(db_session)
    
    # Create test role
    role_data = RoleCreate(
        name="delete_role_test",
        description="Test role for deletion",
        permissions=[]
    )
    created_role = role_service.create_role(role_data)
    
    # Delete role
    role_service.delete_role(created_role.id)
    
    # Verify deletion
    deleted_role = role_service.get_role(created_role.id)
    assert deleted_role is None

def test_assign_permissions(db_session):
    """Test assigning permissions to a role."""
    role_service = RoleService(db_session)
    
    # Create test role
    role_data = RoleCreate(
        name="permission_test_role",
        description="Test role for permission assignment",
        permissions=[]
    )
    role = role_service.create_role(role_data)
    
    # Create test permissions
    permission1 = Permission(
        name="test:read",
        description="Test read permission",
        resource="test",
        action="read",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    permission2 = Permission(
        name="test:write",
        description="Test write permission",
        resource="test",
        action="write",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add_all([permission1, permission2])
    db_session.commit()
    
    # Assign permissions
    permissions = [permission1.id, permission2.id]
    role_service.assign_permissions(role.id, permissions)
    
    # Verify assignments
    role_permissions = [p.id for p in role.permissions]
    assert permission1.id in role_permissions
    assert permission2.id in role_permissions

def test_get_role_permissions(db_session):
    """Test getting role permissions."""
    role_service = RoleService(db_session)
    
    # Create test permissions
    permission1 = Permission(
        name="test:read",
        description="Test read permission",
        resource="test",
        action="read",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    permission2 = Permission(
        name="test:write",
        description="Test write permission",
        resource="test",
        action="write",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add_all([permission1, permission2])
    db_session.commit()
    
    # Create test role with permissions
    role_data = RoleCreate(
        name="get_permissions_test_role",
        description="Test role for getting permissions",
        permissions=[permission1.id, permission2.id]
    )
    role = role_service.create_role(role_data)
    
    # Get permissions
    permissions = role_service.get_role_permissions(role.id)
    
    assert len(permissions) == 2
    permission_ids = [p.id for p in permissions]
    assert permission1.id in permission_ids
    assert permission2.id in permission_ids
