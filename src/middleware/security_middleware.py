"""Security middleware for FastAPI application."""
from fastapi import Request
from fastapi.responses import Response
import logging
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from src.core.config import settings

# Configure logging
logger = logging.getLogger(__name__)

class SecurityMiddleware(BaseHTTPMiddleware):
    """Security middleware for enforcing security headers and policies."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """Add security headers to response."""
        response = await call_next(request)
        
        # Add security headers from configuration
        for header, value in settings.SECURITY_HEADERS.items():
            response.headers[header] = value
        
        # Cache Control for API endpoints
        if request.url.path.startswith("/api/"):
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, proxy-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
        
        return response

def setup_security_middleware(app):
    """Add security middleware to FastAPI app."""
    app.add_middleware(SecurityMiddleware)
