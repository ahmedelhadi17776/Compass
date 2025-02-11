import sys
import os
import traceback

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv(dotenv_path=os.path.join(project_root, 'configs', '.env'))

def verify_database_connection():
    try:
        # Get database URL from environment variables
        db_user = os.getenv('DB_USER')
        db_password = os.getenv('DB_PASSWORD')
        db_host = os.getenv('DB_HOST')
        db_port = os.getenv('DB_PORT')
        db_name = os.getenv('DB_NAME')

        # Construct the database URL
        database_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        
        # Create engine
        engine = create_engine(database_url)
        
        # Test connection
        with engine.connect() as connection:
            # Simple query to check connection
            result = connection.execute(text("SELECT current_database()"))
            db_name = result.scalar()
            logger.info(f"Successfully connected to database: {db_name}")
            
            # List all tables in the database
            tables_query = text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
            """)
            tables = connection.execute(tables_query).fetchall()
            
            if tables:
                logger.info("Tables in the database:")
                for table in tables:
                    logger.info(f"Table: {table[0]}")
                    
                    # Count rows in each table
                    row_count_query = text(f"SELECT COUNT(*) FROM {table[0]}")
                    row_count = connection.execute(row_count_query).scalar()
                    logger.info(f"  Rows in {table[0]}: {row_count}")
            else:
                logger.warning("No tables found in the database")
        
        return True
    
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    if verify_database_connection():
        sys.exit(0)
    else:
        sys.exit(1)
