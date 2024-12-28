import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler

from .config import settings

# Create logs directory if it doesn't exist
logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)

# Configure logging


def setup_logging():
    """Configure logging for the application."""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    formatter = logging.Formatter(log_format)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler for auth.log
    auth_handler = RotatingFileHandler(
        logs_dir / "auth.log",
        maxBytes=10485760,  # 10MB
        backupCount=5
    )
    auth_handler.setFormatter(formatter)
    auth_logger = logging.getLogger("auth")
    auth_logger.addHandler(auth_handler)
    auth_logger.setLevel(logging.INFO)

    # File handler for error.log
    error_handler = RotatingFileHandler(
        logs_dir / "error.log",
        maxBytes=10485760,  # 10MB
        backupCount=5
    )
    error_handler.setFormatter(formatter)
    error_handler.setLevel(logging.ERROR)
    root_logger.addHandler(error_handler)

    return root_logger
