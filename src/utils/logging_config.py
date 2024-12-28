"""
Logging configuration and setup.
"""
import logging
from src.core.config import settings


def setup_logging():
    """Set up application-wide logging."""
    logger = logging.getLogger("aiwa")
    logger.setLevel(settings.LOG_LEVEL)

    # Console Handler
    ch = logging.StreamHandler()
    ch.setLevel(settings.LOG_LEVEL)
    formatter = logging.Formatter(settings.LOG_FORMAT)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File Handler
    fh = logging.FileHandler("logs/aiwa.log")
    fh.setLevel(logging.INFO)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # Avoid duplicate logs
    logger.propagate = False
