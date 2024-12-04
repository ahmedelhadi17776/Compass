from src.data.database.connection import engine
from src.data.database.models import Base, User, Role, Permission, TaskStatus, TaskPriority, TaskCategory, Tag, user_roles, role_permissions
from sqlalchemy.orm import Session
from sqlalchemy import text
from src.services.authentication.auth_service import AuthService
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_default_admin():
    """Create a default admin user if none exists."""
    db = Session(engine)
    try:
        # Create default role if it doesn't exist
        admin_role = db.query(Role).filter(Role.name == "admin").first()
        if not admin_role:
            admin_role = Role(
                name="admin",
                description="Administrator role with full access"
            )
            db.add(admin_role)
            db.commit()
            db.refresh(admin_role)
            logger.info("Default admin role created successfully!")

        # Check if admin exists
        admin = db.query(User).filter(User.email == "admin@aiwa.com").first()
        if not admin:
            auth_service = AuthService(db)
            admin_password = os.getenv("ADMIN_PASSWORD", "admin123")  # Default password if not in env
            
            # Create admin user
            admin = User(
                username="admin",
                email="admin@aiwa.com",
                hashed_password=auth_service.get_password_hash(admin_password),
                is_active=True,
                role_id=admin_role.id
            )
            db.add(admin)
            db.commit()
            logger.info("Default admin user created successfully!")
    except Exception as e:
        logger.error(f"Error creating admin user: {e}")
        db.rollback()
    finally:
        db.close()

def init_db():
    """Initialize the database."""
    try:
        # Drop tables in reverse dependency order
        logger.info("Dropping existing tables...")
        
        # Get all tables in reverse dependency order
        tables = Base.metadata.sorted_tables
        if engine.dialect.name == 'postgresql':
            # For PostgreSQL, disable foreign key checks while dropping
            with engine.connect() as conn:
                with conn.begin():
                    conn.execute(text("SET CONSTRAINTS ALL DEFERRED"))
                    for table in reversed(tables):
                        conn.execute(text(f'DROP TABLE IF EXISTS {table.name} CASCADE'))
                    conn.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
        else:
            # For other databases
            Base.metadata.drop_all(bind=engine)
        
        logger.info("Dropped all existing tables.")
        
        # Create tables in dependency order
        logger.info("Creating tables...")
        
        # 1. Create base tables (no foreign keys)
        for table in [Role.__table__, Permission.__table__, TaskStatus.__table__, 
                     TaskPriority.__table__, TaskCategory.__table__, Tag.__table__]:
            table.create(bind=engine)
        logger.info("Created base tables")
        
        # 2. Create User table (depends on roles)
        User.__table__.create(bind=engine)
        logger.info("Created user table")
        
        # 3. Create association tables
        for table in [user_roles, role_permissions]:
            table.create(bind=engine)
        logger.info("Created association tables")
        
        # 4. Create all remaining tables
        Base.metadata.create_all(bind=engine)
        logger.info("Created all remaining tables")
        
        # Create default admin user
        create_default_admin()
        
        logger.info("Database initialization completed successfully!")
        
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise  # Re-raise the exception for better error handling

if __name__ == "__main__":
    init_db()
