"""
Global error handling utilities.
"""
import logging
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from src.core.logging import logger

logger = logging.getLogger(__name__)


def handle_error(error: Exception, context: str = None):
    """Global error handler."""
    logger.error(f"Error in {context}: {str(error)}")
    # TODO: Implement error handling logic
    pass


async def generic_exception_handler(request: Request, exc: Exception):
    """Handle generic exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    logger.warning(f"HTTP exception occurred: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )
