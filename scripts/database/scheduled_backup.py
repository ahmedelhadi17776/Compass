"""
Script to perform database backup and cleanup.
Can be scheduled using Windows Task Scheduler.
"""
from pathlib import Path
import sys
import logging
from datetime import datetime

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logging_config import setup_logging
from scripts.database.backup import backup_database, cleanup_old_backups

# Set up logging
setup_logging()
logger = logging.getLogger(__name__)

def daily_backup():
    """Perform daily backup and cleanup."""
    try:
        logger.info("Starting scheduled daily backup")
        
        # Create backup
        backup_file = backup_database()
        logger.info(f"Daily backup created: {backup_file}")
        
        # Clean up old backups
        cleanup_old_backups(days=5)
        logger.info("Old backup cleanup completed")
        
    except Exception as e:
        logger.error(f"Scheduled backup failed: {e}")

if __name__ == "__main__":
    daily_backup()
