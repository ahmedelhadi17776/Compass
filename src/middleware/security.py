"""Security middleware."""
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import logging
from src.core.security.headers import SecurityHeadersService
from src.core.security.exceptions import SecurityError

logger = logging.getLogger(__name__)


class SecurityMiddleware(BaseHTTPMiddleware):
    """Middleware for applying security measures."""

    def __init__(self, app, security_service=None):
        super().__init__(app)
        self.security_service = security_service
        self.headers_service = SecurityHeadersService()

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process the request."""
        try:
            # Store security service in request state
            if self.security_service:
                request.state.security_service = self.security_service

            # Process request
            response = await call_next(request)

            # Add security headers
            self.headers_service.apply_security_headers(response)

            return response

        except Exception as e:
            logger.error(f"Security error: {str(e)}")
            if isinstance(e, SecurityError):
                raise
            raise SecurityError(detail="Security check failed")
