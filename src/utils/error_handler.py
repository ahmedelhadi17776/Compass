"""
Global error handling utilities.
"""
import logging

logger = logging.getLogger(__name__)

def handle_error(error: Exception, context: str = None):
    """Global error handler."""
    logger.error(f"Error in {context}: {str(error)}")
    # TODO: Implement error handling logic
    pass
