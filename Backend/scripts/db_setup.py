import os
import sys
import logging
import psycopg2
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError, OperationalError
import traceback

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

from Backend.data.database.models import Base
from Backend.data.database.connection import DATABASE_URL, DB_USER, DB_NAME, DB_HOST, DB_PASSWORD, DB_PORT

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_database():
    """Create the database if it doesn't exist."""
    try:
        # Use psycopg2 to connect to the default postgres database as postgres superuser
        conn = psycopg2.connect(
            dbname='postgres', 
            user='postgres', 
            password='0502747598', 
            host=DB_HOST, 
            port=DB_PORT
        )
        conn.autocommit = True
        cur = conn.cursor()
        
        # Check if database exists
        cur.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{DB_NAME}'")
        if not cur.fetchone():
            cur.execute(f'CREATE DATABASE "{DB_NAME}"')
            logger.info(f"Database {DB_NAME} created successfully.")
        else:
            logger.info(f"Database {DB_NAME} already exists.")
        
        # Create the user if not exists
        cur.execute(f"SELECT 1 FROM pg_catalog.pg_roles WHERE rolname = '{DB_USER}'")
        if not cur.fetchone():
            cur.execute(f'CREATE USER "{DB_USER}" WITH PASSWORD \'{DB_PASSWORD}\'')
            logger.info(f"User {DB_USER} created successfully.")
        
        cur.close()
        conn.close()
    except Exception as e:
        logger.error(f"Error creating database: {e}")
        traceback.print_exc()
        raise

def grant_database_permissions():
    """Grant necessary permissions to the database user."""
    try:
        # Use psycopg2 to connect as postgres superuser
        conn = psycopg2.connect(
            dbname='postgres', 
            user='postgres', 
            password='0502747598', 
            host=DB_HOST, 
            port=DB_PORT
        )
        conn.autocommit = True
        cur = conn.cursor()
        
        # Connect to the specific database
        db_conn = psycopg2.connect(
            dbname=DB_NAME, 
            user='postgres', 
            password='0502747598', 
            host=DB_HOST, 
            port=DB_PORT
        )
        db_conn.autocommit = True
        db_cur = db_conn.cursor()
        
        # Grant all privileges on the database
        cur.execute(f'GRANT ALL PRIVILEGES ON DATABASE "{DB_NAME}" TO "{DB_USER}"')
        
        # Grant all privileges on the schema and future objects
        db_cur.execute(f'GRANT ALL PRIVILEGES ON SCHEMA public TO "{DB_USER}"')
        db_cur.execute(f'GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO "{DB_USER}"')
        db_cur.execute(f'GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO "{DB_USER}"')
        db_cur.execute(f'GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO "{DB_USER}"')
        
        # Set default privileges for future objects
        db_cur.execute(f'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON TABLES TO "{DB_USER}"')
        db_cur.execute(f'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON SEQUENCES TO "{DB_USER}"')
        db_cur.execute(f'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON FUNCTIONS TO "{DB_USER}"')
        
        logger.info(f"Granted all necessary permissions to user {DB_USER}")
        
        cur.close()
        conn.close()
        db_cur.close()
        db_conn.close()
    except Exception as e:
        logger.error(f"Error granting database permissions: {e}")
        traceback.print_exc()
        raise

def drop_all_tables_and_schemas():
    """Drop all tables, sequences, types, and schemas in the public schema."""
    try:
        # Use psycopg2 to connect to the database
        conn = psycopg2.connect(
            dbname=DB_NAME, 
            user='postgres', 
            password='0502747598', 
            host=DB_HOST, 
            port=DB_PORT
        )
        conn.autocommit = True
        cur = conn.cursor()
        
        # Drop Alembic version table first
        cur.execute("DROP TABLE IF EXISTS alembic_version CASCADE")
        
        # Drop all tables
        cur.execute("""
            DO $$ 
            DECLARE
                r RECORD;
            BEGIN
                FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
                    EXECUTE 'DROP TABLE IF EXISTS public.' || quote_ident(r.tablename) || ' CASCADE';
                END LOOP;
            END $$;
        """)
        
        # Drop all sequences
        cur.execute("""
            DO $$ 
            DECLARE
                r RECORD;
            BEGIN
                FOR r IN (SELECT sequencename FROM pg_sequences WHERE schemaname = 'public') LOOP
                    EXECUTE 'DROP SEQUENCE IF EXISTS public.' || quote_ident(r.sequencename) || ' CASCADE';
                END LOOP;
            END $$;
        """)
        
        # Drop all types
        cur.execute("""
            DO $$ 
            DECLARE
                r RECORD;
            BEGIN
                FOR r IN (
                    SELECT typname 
                    FROM pg_type t 
                    JOIN pg_namespace n ON n.oid = t.typnamespace 
                    WHERE n.nspname = 'public' 
                    AND t.typtype = 'e'
                ) LOOP
                    EXECUTE 'DROP TYPE IF EXISTS public.' || quote_ident(r.typname) || ' CASCADE';
                END LOOP;
            END $$;
        """)
        
        logger.info("All tables, sequences, and types dropped successfully.")
        
        cur.close()
        conn.close()
    except Exception as e:
        logger.error(f"Error dropping tables, sequences, and types: {e}")
        traceback.print_exc()
        raise

def initialize_database():
    """Initialize the database schema."""
    try:
        engine = create_engine(DATABASE_URL)
        
        # Drop all existing tables, sequences, and types
        drop_all_tables_and_schemas()
        
        # Create all tables defined in the models
        Base.metadata.create_all(engine)
        logger.info("Database schema created successfully.")
        
    except SQLAlchemyError as e:
        logger.error(f"Database initialization error: {e}")
        traceback.print_exc()
        raise

def run_migrations():
    """Run Alembic migrations."""
    try:
        # Ensure Alembic configuration is loaded
        from alembic.config import Config
        from alembic import command
        
        alembic_cfg = Config(os.path.join(project_root, 'src/data/database/migrations/alembic.ini'))
        
        # Set the script location for migrations
        alembic_cfg.set_main_option('script_location', os.path.join(project_root, 'src/data/database/migrations'))
        
        # Manually create the alembic_version table if it doesn't exist
        engine = create_engine(DATABASE_URL)
        with engine.connect() as connection:
            connection.execute(text('''
                CREATE TABLE IF NOT EXISTS alembic_version (
                    version_num VARCHAR(32) NOT NULL,
                    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
                )
            '''))
        
        # Stamp the base revision
        command.stamp(alembic_cfg, "base")
        
        # Upgrade to head
        command.upgrade(alembic_cfg, "head")
        
        logger.info("Migrations completed successfully.")
    except Exception as e:
        logger.error(f"Error running migrations: {e}")
        logger.error(traceback.format_exc())
        raise

def main():
    try:
        create_database()
        grant_database_permissions()
        initialize_database()
        run_migrations()
        logger.info("Database setup completed successfully!")
    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
