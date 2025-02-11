"""Database seeding script for initial data."""
import sys
import os
from pathlib import Path
from datetime import datetime

# Add project root to Python path
project_root = str(Path(__file__).resolve().parents[2])
sys.path.insert(0, project_root)

from sqlalchemy.orm import Session
from Backend.data.database.models import Role, Permission, role_permissions, TaskStatus, TaskPriority
from Backend.data.database.connection import get_db
from Backend.services.authorization.role_service import RoleService
from Backend.services.authorization.permission_service import PermissionService
from Backend.application.schemas.role import RoleCreate
from Backend.application.schemas.permission import PermissionCreate

def seed_roles(db: Session):
    """Seed default roles."""
    roles = [
        {"name": "admin", "description": "System administrator with full access"},
        {"name": "user", "description": "Regular user with standard access"},
        {"name": "manager", "description": "Project manager with team management access"}
    ]
    
    role_service = RoleService(db)
    for role_data in roles:
        if not role_service.get_role_by_name(role_data["name"]):
            role_model = RoleCreate(**role_data)
            role_service.create_role(role_model)
    print("[OK] Roles seeded successfully")

def seed_permissions(db: Session):
    """Seed default permissions."""
    permissions = [
        # User management permissions
        {"name": "user:create", "description": "Create new users", "resource": "user", "action": "create"},
        {"name": "user:read", "description": "View user details", "resource": "user", "action": "read"},
        {"name": "user:update", "description": "Update user details", "resource": "user", "action": "update"},
        {"name": "user:delete", "description": "Delete users", "resource": "user", "action": "delete"},
        
        # Task management permissions
        {"name": "task:create", "description": "Create new tasks", "resource": "task", "action": "create"},
        {"name": "task:read", "description": "View tasks", "resource": "task", "action": "read"},
        {"name": "task:update", "description": "Update tasks", "resource": "task", "action": "update"},
        {"name": "task:delete", "description": "Delete tasks", "resource": "task", "action": "delete"},
        
        # Workflow permissions
        {"name": "workflow:create", "description": "Create workflows", "resource": "workflow", "action": "create"},
        {"name": "workflow:read", "description": "View workflows", "resource": "workflow", "action": "read"},
        {"name": "workflow:update", "description": "Update workflows", "resource": "workflow", "action": "update"},
        {"name": "workflow:delete", "description": "Delete workflows", "resource": "workflow", "action": "delete"}
    ]
    
    permission_service = PermissionService(db)
    for perm_data in permissions:
        if not permission_service.get_permission_by_name(perm_data["name"]):
            perm_model = PermissionCreate(**perm_data)
            permission_service.create_permission(perm_model)
    print("[OK] Permissions seeded successfully")

def assign_role_permissions(db: Session):
    """Assign default permissions to roles."""
    role_service = RoleService(db)
    permission_service = PermissionService(db)
    
    # Admin role gets all permissions
    admin_role = role_service.get_role_by_name("admin")
    if admin_role:
        permissions = permission_service.list_permissions(skip=0, limit=100)
        for permission in permissions:
            try:
                role_service.assign_permission_to_role(admin_role.id, permission.id)
            except Exception:
                # Skip if permission already assigned
                continue
    
    # User role gets basic permissions
    user_role = role_service.get_role_by_name("user")
    if user_role:
        basic_permissions = [
            "task:read",
            "task:create",
            "task:update",
            "workflow:read"
        ]
        for perm_name in basic_permissions:
            perm = permission_service.get_permission_by_name(perm_name)
            if perm:
                try:
                    role_service.assign_permission_to_role(user_role.id, perm.id)
                except Exception:
                    continue
    
    # Manager role gets team management permissions
    manager_role = role_service.get_role_by_name("manager")
    if manager_role:
        manager_permissions = [
            "task:create", "task:read", "task:update", "task:delete",
            "workflow:create", "workflow:read", "workflow:update",
            "user:read"
        ]
        for perm_name in manager_permissions:
            perm = permission_service.get_permission_by_name(perm_name)
            if perm:
                try:
                    role_service.assign_permission_to_role(manager_role.id, perm.id)
                except Exception:
                    continue
    
    print("[OK] Role permissions assigned successfully")

def seed_task_statuses(db: Session):
    """Seed default task statuses."""
    statuses = [
        {"name": "TODO", "description": "Task is pending", "color_code": "#FF0000"},
        {"name": "IN_PROGRESS", "description": "Task is being worked on", "color_code": "#FFA500"},
        {"name": "REVIEW", "description": "Task is under review", "color_code": "#0000FF"},
        {"name": "DONE", "description": "Task is completed", "color_code": "#00FF00"}
    ]
    
    for status_data in statuses:
        existing = db.query(TaskStatus).filter(TaskStatus.name == status_data["name"]).first()
        if not existing:
            status = TaskStatus(**status_data)
            db.add(status)
    
    try:
        db.commit()
        print("[OK] Task statuses seeded successfully")
    except Exception as e:
        db.rollback()
        print(f"Error seeding task statuses: {str(e)}")

def seed_task_priorities(db: Session):
    """Seed default task priorities."""
    priorities = [
        {"name": "LOW", "description": "Low priority task", "color_code": "#808080"},
        {"name": "MEDIUM", "description": "Medium priority task", "color_code": "#FFA500"},
        {"name": "HIGH", "description": "High priority task", "color_code": "#FF0000"},
        {"name": "URGENT", "description": "Urgent priority task", "color_code": "#8B0000"}
    ]
    
    for priority_data in priorities:
        existing = db.query(TaskPriority).filter(TaskPriority.name == priority_data["name"]).first()
        if not existing:
            priority = TaskPriority(**priority_data)
            db.add(priority)
    
    try:
        db.commit()
        print("[OK] Task priorities seeded successfully")
    except Exception as e:
        db.rollback()
        print(f"Error seeding task priorities: {str(e)}")

def main():
    """Main entry point for database seeding."""
    print("Starting database seeding...")
    try:
        db = next(get_db())
        seed_roles(db)
        seed_permissions(db)
        assign_role_permissions(db)
        seed_task_statuses(db)
        seed_task_priorities(db)
        print("Database seeding completed successfully!")
    except Exception as e:
        print(f"Error seeding database: {str(e)}")
        raise

if __name__ == "__main__":
    main()
