import logging
from src.utils.logging_config import setup_logging
from src.utils.error_handler import handle_error
from dotenv import load_dotenv
import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path
import shutil
import argparse
import gzip

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


# Set up logging
setup_logging()
logger = logging.getLogger(__name__)


def compress_file(input_file):
    """Compress a file using gzip."""
    output_file = str(input_file) + '.gz'
    with open(input_file, 'rb') as f_in:
        with gzip.open(output_file, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    os.remove(input_file)
    return output_file


def decompress_file(input_file):
    """Decompress a gzip file."""
    output_file = input_file[:-3]  # Remove .gz extension
    with gzip.open(input_file, 'rb') as f_in:
        with open(output_file, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    return output_file


def create_backup_directory():
    """Create backup directory if it doesn't exist."""
    backup_dir = project_root / 'backups' / 'database'
    backup_dir.mkdir(parents=True, exist_ok=True)
    return backup_dir


def get_backup_filename(prefix='backup'):
    """Generate a backup filename with timestamp."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"{prefix}_{timestamp}.sql"


def backup_database(backup_path=None, custom_name=None):
    """
    Backup the database using pg_dump.

    Args:
        backup_path (str, optional): Custom backup path. Defaults to None.
        custom_name (str, optional): Custom backup file name. Defaults to None.
    """
    try:
        # Load environment variables
        load_dotenv(os.path.join(project_root, 'configs', '.env'))

        # Add PostgreSQL bin directory to PATH
        postgres_path = r"D:\Programs\PostgreSQL\17\bin"
        if postgres_path not in os.environ["PATH"]:
            os.environ["PATH"] = postgres_path + \
                os.pathsep + os.environ["PATH"]

        # Get database configuration
        db_user = os.getenv("DB_USER")
        db_password = os.getenv("DB_PASSWORD")
        db_name = os.getenv("DB_NAME")
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = os.getenv("DB_PORT", "5432")

        # Create backup directory if it doesn't exist
        backup_dir = create_backup_directory()

        # Get backup filename
        backup_file = get_backup_filename(
            custom_name) if custom_name else get_backup_filename()
        final_backup_path = backup_path if backup_path else os.path.join(
            backup_dir, backup_file)

        logger.info(f"Starting database backup to {final_backup_path}")

        # Build the pg_dump command with additional options
        cmd = [
            'pg_dump',
            '-h', db_host,
            '-p', db_port,
            '-U', db_user,
            '-w',  # Never prompt for password
            '-F', 'c',  # Use custom format
            '-b',  # Include large objects
            '-v',  # Verbose mode
            '-d', db_name,
            '-f', final_backup_path
        ]

        # Execute pg_dump
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            # Set password in environment
            env=dict(os.environ, PGPASSWORD=db_password)
        )

        stdout, stderr = process.communicate()

        if process.returncode != 0:
            raise Exception(f"pg_dump failed: {stderr.decode()}")

        # Compress the backup
        compressed_file = compress_file(final_backup_path)
        logger.info(f"Database backup completed successfully: {
                    compressed_file}")
        return compressed_file

    except Exception as e:
        error_msg = f"Error in Database backup: {str(e)}"
        logger.error(error_msg)
        handle_error(e)
        return False


def restore_database(backup_file):
    """
    Restore the database from a backup file.

    Args:
        backup_file (str): Path to the backup file
    """
    try:
        # Load environment variables from configs directory
        load_dotenv(project_root / 'configs' / '.env')

        # Get database configuration
        db_user = os.getenv("DB_USER")
        db_password = os.getenv("DB_PASSWORD")
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = os.getenv("DB_PORT", "5432")
        db_name = os.getenv("DB_NAME", "aiwa_dev")

        # Set PGPASSWORD environment variable
        os.environ['PGPASSWORD'] = db_password

        backup_path = Path(backup_file)

        # Decompress if it's a .gz file
        if backup_file.endswith('.gz'):
            logger.info("Decompressing backup file...")
            backup_path = Path(decompress_file(backup_file))

        # Construct pg_restore command
        command = [
            'pg_restore',
            '-h', db_host,
            '-p', db_port,
            '-U', db_user,
            '-d', db_name,
            '-v',  # Verbose
            '-c',  # Clean (drop) database objects before recreating
            '-F', 'c',  # Custom format
            str(backup_path)
        ]

        # Execute restore
        logger.info(f"Starting database restore from {backup_file}")
        result = subprocess.run(command, capture_output=True, text=True)

        if result.returncode == 0:
            logger.info("Database restore completed successfully")
        else:
            # pg_restore often returns non-zero even on success, check if there are real errors
            if "error:" in result.stderr.lower():
                raise Exception(f"Restore failed: {result.stderr}")
            else:
                logger.warning("Restore completed with warnings:")
                logger.warning(result.stderr)

    except Exception as e:
        handle_error(e, "Database restore")
        logger.error(f"Database restore failed: {e}")
        raise
    finally:
        # Clear PGPASSWORD
        os.environ['PGPASSWORD'] = ''
        # Clean up decompressed file if it was compressed
        if backup_file.endswith('.gz') and backup_path.exists():
            backup_path.unlink()


def list_backups():
    """List all available database backups."""
    backup_dir = project_root / 'backups' / 'database'
    if not backup_dir.exists():
        print("No backups found.")
        return

    backups = sorted(backup_dir.glob('*.gz'),
                     key=lambda x: x.stat().st_mtime, reverse=True)
    if not backups:
        print("No backups found.")
        return

    print("\nAvailable backups:")
    print("-" * 80)
    print(f"{'Filename':<50} {'Size':<10} {'Date':<20}")
    print("-" * 80)

    for backup in backups:
        size = backup.stat().st_size
        size_str = f"{size/1024/1024:.2f} MB"
        date = datetime.fromtimestamp(
            backup.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        print(f"{backup.name:<50} {size_str:<10} {date:<20}")


def cleanup_old_backups(days=7):
    """Remove backups older than specified days."""
    try:
        backup_dir = project_root / 'backups' / 'database'
        if not backup_dir.exists():
            return

        current_time = datetime.now().timestamp()
        deleted_count = 0

        for backup in backup_dir.glob('*.gz'):
            file_age_days = (
                current_time - backup.stat().st_mtime) / (24 * 3600)
            if file_age_days > days:
                backup.unlink()
                deleted_count += 1
                logger.info(f"Deleted old backup: {backup.name}")

        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} old backup(s)")

    except Exception as e:
        handle_error(e, "Backup cleanup")
        logger.error(f"Backup cleanup failed: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Database Backup and Restore Utility')
    parser.add_argument('action', choices=['backup', 'restore', 'list', 'cleanup'],
                        help='Action to perform')
    parser.add_argument('--file', help='Backup file path for restore')
    parser.add_argument('--name', help='Custom name for backup file')
    parser.add_argument('--days', type=int, default=7,
                        help='Days threshold for cleanup (default: 7)')

    args = parser.parse_args()

    try:
        if args.action == 'backup':
            backup_database(custom_name=args.name)
            print("Backup created successfully")

        elif args.action == 'restore':
            if not args.file:
                print("Error: --file argument is required for restore")
                sys.exit(1)
            restore_database(args.file)
            print("Restore completed successfully")

        elif args.action == 'list':
            list_backups()

        elif args.action == 'cleanup':
            cleanup_old_backups(args.days)
            print(f"Cleaned up backups older than {args.days} days")

    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
