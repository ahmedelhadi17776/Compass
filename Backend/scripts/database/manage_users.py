import os
import sys
from pathlib import Path
import argparse
import getpass

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from Backend.services.authentication.auth_service import AuthService
from Backend.data.database.connection import get_db
from Backend.core.security import HashManager
from Backend.data.database.models import User, Role
from Backend.application.schemas.user import UserCreate
from Backend.utils.logging_config import setup_logging
import logging

# Set up logging
setup_logging()
logger = logging.getLogger(__name__)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="User management script")
    subparsers = parser.add_subparsers(dest="action", help="Action to perform")

    # Create admin command
    create_admin_parser = subparsers.add_parser("create-admin", help="Create a new admin user")
    create_admin_parser.add_argument("--username", help="Admin username")
    create_admin_parser.add_argument("--email", help="Admin email")
    create_admin_parser.add_argument("--password", help="Admin password")
    create_admin_parser.add_argument("--first-name", help="Admin first name")
    create_admin_parser.add_argument("--last-name", help="Admin last name")

    # Reset password command
    reset_parser = subparsers.add_parser("reset-password", help="Reset a user's password")
    reset_parser.add_argument("username", help="Username of the account")

    # List users command
    list_parser = subparsers.add_parser("list-users", help="List all users")

    # Deactivate user command
    deactivate_parser = subparsers.add_parser("deactivate-user", help="Deactivate a user account")
    deactivate_parser.add_argument("username", help="Username of the account to deactivate")

    return parser.parse_args()

def create_admin():
    """Create a new admin user."""
    print("\nCreating new admin user...")
    args = parse_args()
    
    # Get command line arguments if provided, otherwise use input
    if args.username and args.email and args.password and args.first_name and args.last_name:
        username = args.username
        email = args.email
        password = args.password
        first_name = args.first_name
        last_name = args.last_name
    else:
        username = input("Enter username: ")
        email = input("Enter email: ")
        password = getpass.getpass("Enter password: ")
        confirm_password = getpass.getpass("Confirm password: ")
        if password != confirm_password:
            print("Error: Passwords do not match")
            return False
        first_name = input("Enter first name: ")
        last_name = input("Enter last name: ")

    try:
        db = next(get_db())
        auth_service = AuthService(db)
        
        # Check if admin role exists
        admin_role = db.query(Role).filter(Role.name == 'admin').first()
        if not admin_role:
            admin_role = Role(
                name="admin",
                description="Administrator role with full access"
            )
            db.add(admin_role)
            db.commit()
            db.refresh(admin_role)
            logger.info("Created admin role")
        
        # Create user using UserCreate schema
        user_data = UserCreate(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        # Create user
        user = auth_service.create_user(user_data)
        
        # Assign admin role
        user.roles.append(admin_role)
        db.commit()
        
        print(f"\nAdmin user '{username}' created successfully!")
        return True
        
    except Exception as e:
        print(f"\nError creating admin user: {str(e)}")
        return False

def reset_password():
    """Reset a user's password."""
    print("\nResetting user password...")
    args = parse_args()
    username = args.username
    new_password = getpass.getpass("Enter new password: ")
    confirm_password = getpass.getpass("Confirm new password: ")

    if new_password != confirm_password:
        print("Error: Passwords do not match")
        return False

    try:
        db = next(get_db())
        auth_service = AuthService(db)
        
        # Get user
        user = auth_service.get_user(username)
        if not user:
            print(f"Error: User '{username}' not found")
            return False
            
        # Update password
        user.hashed_password = HashManager.hash_password(new_password)
        db.commit()
        
        print(f"\nPassword reset successful for user '{username}'!")
        return True
        
    except Exception as e:
        print(f"\nError resetting password: {str(e)}")
        return False

def list_users():
    """List all users in the system."""
    try:
        db = next(get_db())
        
        users = db.query(User).all()
        
        print("\nUsers in the system:")
        print("Username | Email | Full Name | Roles | Active")
        print("-" * 70)
        
        for user in users:
            roles = ", ".join([role.name for role in user.roles]) if user.roles else "No roles"
            full_name = f"{user.first_name or ''} {user.last_name or ''}".strip() or "N/A"
            print(f"{user.username} | {user.email} | {full_name} | "
                  f"{roles} | {'Yes' if user.is_active else 'No'}")
                  
        return True
        
    except Exception as e:
        print(f"\nError listing users: {str(e)}")
        return False

def deactivate_user():
    """Deactivate a user account."""
    print("\nDeactivating user account...")
    args = parse_args()
    username = args.username

    try:
        db = next(get_db())
        auth_service = AuthService(db)
        
        # Get user
        user = auth_service.get_user(username)
        if not user:
            print(f"Error: User '{username}' not found")
            return False
            
        # Deactivate user
        user.is_active = False
        db.commit()
        
        print(f"\nUser '{username}' has been deactivated!")
        return True
        
    except Exception as e:
        print(f"\nError deactivating user: {str(e)}")
        return False

def main():
    args = parse_args()

    actions = {
        'create-admin': create_admin,
        'reset-password': reset_password,
        'list-users': list_users,
        'deactivate-user': deactivate_user
    }

    if not actions[args.action]():
        sys.exit(1)

if __name__ == "__main__":
    main()
