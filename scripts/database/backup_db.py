"""
Database backup script.
"""
import os
import subprocess
from datetime import datetime
import logging
from logging.config import fileConfig
import sys

# Add the project root directory to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

# Setup logging
fileConfig(os.path.join(project_root, 'configs', 'logging_config.json'))
logger = logging.getLogger(__name__)

def create_backup():
    """Create a backup of the database."""
    try:
        timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        backup_dir = os.path.join(project_root, 'backups', 'database')
        backup_file = os.path.join(backup_dir, f'aiwa_db_{timestamp}_name_fields_update.sql')
        
        # Ensure backup directory exists
        os.makedirs(backup_dir, exist_ok=True)
        
        # Create backup using pg_dump
        cmd = [
            'pg_dump',
            '-U', 'postgres',
            '-d', 'aiwa_db',
            '-f', backup_file
        ]
        
        subprocess.run(cmd, check=True)
        logger.info(f"Database backup created successfully at: {backup_file}")
        return True
    except Exception as e:
        logger.error(f"Error creating database backup: {str(e)}")
        return False

if __name__ == '__main__':
    create_backup()
