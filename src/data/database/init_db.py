from src.data.database.connection import engine
from src.data.database.models import (
    Base, User, Role, Permission, 
    TaskStatus, TaskCategory, 
    Tag, role_permissions, task_tags, UserRole
)
from sqlalchemy.orm import Session
from sqlalchemy import text
from src.services.authentication.auth_service import AuthService
import os
import secrets
import logging
from dotenv import load_dotenv
from enum import Enum, auto

# Load environment variables from the configs directory
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'configs', '.env'))

# Set up logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')), 
    format=os.getenv('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
)
logger = logging.getLogger(__name__)

class DatabaseInitMode(Enum):
    """Enumeration for database initialization modes."""
    DEV = auto()
    PROD = auto()
    TEST = auto()

def generate_secure_admin_password(length=24):
    """Generate a cryptographically secure random password."""
    return secrets.token_urlsafe(length)

def create_default_permissions():
    """Create a comprehensive set of default permissions."""
    db = Session(engine)
    try:
        default_permissions = [
            # User Permissions
            Permission(name="user_create", resource="user", action="create"),
            Permission(name="user_read", resource="user", action="read"),
            Permission(name="user_update", resource="user", action="update"),
            Permission(name="user_delete", resource="user", action="delete"),
            
            # Task Permissions
            Permission(name="task_create", resource="task", action="create"),
            Permission(name="task_read", resource="task", action="read"),
            Permission(name="task_update", resource="task", action="update"),
            Permission(name="task_delete", resource="task", action="delete"),
            
            # Workflow Permissions
            Permission(name="workflow_create", resource="workflow", action="create"),
            Permission(name="workflow_read", resource="workflow", action="read"),
            Permission(name="workflow_update", resource="workflow", action="update"),
            Permission(name="workflow_delete", resource="workflow", action="delete"),
            
            # Admin Permissions
            Permission(name="admin_full_access", resource="system", action="all"),
        ]
        
        # Add permissions if they don't exist
        for perm in default_permissions:
            existing_perm = db.query(Permission).filter(
                Permission.name == perm.name
            ).first()
            if not existing_perm:
                db.add(perm)
        
        db.commit()
        logger.info("Default permissions created successfully!")
        return default_permissions
    except Exception as e:
        logger.error(f"Error creating default permissions: {e}")
        db.rollback()
        return []
    finally:
        db.close()

def create_default_roles(permissions):
    """Create default roles with associated permissions."""
    db = Session(engine)
    try:
        # Create admin role with all permissions
        admin_role = db.query(Role).filter(Role.name == "admin").first()
        if not admin_role:
            admin_role = Role(
                name="admin",
                description="Administrator role with full system access"
            )
            db.add(admin_role)
            db.commit()
            db.refresh(admin_role)
            
            # Attach all permissions to admin role
            admin_permissions = [p for p in permissions if p.name == "admin_full_access"]
            for perm in admin_permissions:
                db.execute(role_permissions.insert().values(
                    role_id=admin_role.id, 
                    permission_id=perm.id
                ))
        
        # Create default user role with limited permissions
        user_role = db.query(Role).filter(Role.name == "user").first()
        if not user_role:
            user_role = Role(
                name="user",
                description="Standard user role with basic access"
            )
            db.add(user_role)
            db.commit()
            db.refresh(user_role)
            
            # Attach basic permissions to user role
            basic_permissions = [
                p for p in permissions 
                if p.name in [
                    "task_create", "task_read", "task_update", 
                    "workflow_read"
                ]
            ]
            for perm in basic_permissions:
                db.execute(role_permissions.insert().values(
                    role_id=user_role.id, 
                    permission_id=perm.id
                ))
        
        db.commit()
        logger.info("Default roles created successfully!")
        return admin_role, user_role
    except Exception as e:
        logger.error(f"Error creating default roles: {e}")
        db.rollback()
        return None, None
    finally:
        db.close()

def create_default_admin(admin_role):
    """Create a secure, configurable default admin user."""
    db = Session(engine)
    try:
        # Check if admin exists
        admin = db.query(User).filter(User.email == os.getenv("ADMIN_EMAIL", "admin@aiwa.com")).first()
        if not admin:
            auth_service = AuthService(db)
            
            # Use environment variable or generate secure password
            admin_password = os.getenv("ADMIN_PASSWORD")
            if not admin_password:
                admin_password = generate_secure_admin_password()
                logger.warning(
                    "Generated a new secure admin password. "
                    "Please store it securely: %s", 
                    admin_password
                )
            
            # Create admin user
            admin = User(
                username=os.getenv("ADMIN_USERNAME", "admin"),
                email=os.getenv("ADMIN_EMAIL", "admin@aiwa.com"),
                full_name="System Administrator",
                hashed_password=auth_service.get_password_hash(admin_password),
                is_active=True,
                is_verified=True
            )
            db.add(admin)
            
            # Attach admin role
            user_role = UserRole(
                user_id=admin.id,
                role_id=admin_role.id
            )
            db.add(user_role)
            
            db.commit()
            logger.info("Default admin user created successfully!")
            return admin
    except Exception as e:
        logger.error(f"Error creating admin user: {e}")
        db.rollback()
    finally:
        db.close()

def init_db(mode=None):
    """Initialize the database with configurable modes."""
    try:
        # Determine initialization mode from environment or parameter
        if mode is None:
            mode_str = os.getenv('DB_INIT_MODE', 'dev').lower()
            mode = {
                'dev': DatabaseInitMode.DEV,
                'prod': DatabaseInitMode.PROD,
                'test': DatabaseInitMode.TEST
            }.get(mode_str, DatabaseInitMode.DEV)
        
        logger.info(f"Initializing database in {mode.name} mode")
        
        # Determine table drop behavior based on mode and environment
        drop_tables = os.getenv('DB_DROP_TABLES', 'true').lower() == 'true'
        if mode in [DatabaseInitMode.DEV, DatabaseInitMode.TEST] and drop_tables:
            logger.info("Dropping existing tables...")
            try:
                Base.metadata.drop_all(bind=engine)
            except Exception as drop_error:
                logger.error(f"Error dropping tables: {drop_error}")
                import traceback
                traceback.print_exc()
                raise
        else:
            logger.info("Skipping table drop in production mode")
        
        # Create tables
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("Tables created successfully")
        except Exception as create_error:
            logger.error(f"Error creating tables: {create_error}")
            import traceback
            traceback.print_exc()
            raise
        
        # Initialize core data
        try:
            with Session(engine) as db:
                # Create permissions
                permissions = create_default_permissions()
                db.add_all(permissions)
                
                # Create roles
                admin_role, user_role = create_default_roles(permissions)
                db.add_all([admin_role, user_role])
                
                # Commit the permissions and roles
                db.commit()
                
                logger.info("Permissions and roles created successfully")
        except Exception as data_error:
            logger.error(f"Error creating default permissions/roles: {data_error}")
            import traceback
            traceback.print_exc()
            raise
        
        # Create admin user only in dev/test modes or if explicitly configured
        create_admin = os.getenv('CREATE_ADMIN', 'true').lower() == 'true'
        if (mode in [DatabaseInitMode.DEV, DatabaseInitMode.TEST] or create_admin) and admin_role:
            try:
                with Session(engine) as db:
                    # Create default admin
                    admin_user = create_default_admin(admin_role)
                    db.add(admin_user)
                    db.commit()
                    logger.info("Admin user created successfully")
            except Exception as admin_error:
                logger.error(f"Error creating admin user: {admin_error}")
                import traceback
                traceback.print_exc()
                raise
        
        logger.info("Database initialization completed successfully!")
        
    except Exception as e:
        logger.error(f"Critical error during database initialization: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    # Default to dev mode when run as a script
    init_db()
