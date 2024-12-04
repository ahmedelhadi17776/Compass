"""
Logging configuration and setup.
"""
import logging
import os
from pathlib import Path

def setup_logging():
    """Set up basic logging configuration."""
    # Create logs directory if it doesn't exist
    log_dir = Path(__file__).parent.parent.parent / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Basic logging configuration
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),  # Console handler
            logging.FileHandler(log_dir / 'app.log')  # File handler
        ]
    )
    
    # Set level for specific loggers
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
