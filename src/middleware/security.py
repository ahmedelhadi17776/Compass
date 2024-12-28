"""Security middleware."""
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import logging
import time
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
        start_time = time.time()

        try:
            # Store security service in request state
            if self.security_service:
                request.state.security_service = self.security_service

            # Check for suspicious activity
            await self.security_service.check_suspicious_activity(request)

            # Process request
            response = await call_next(request)

            # Add security headers
            self.headers_service.apply_security_headers(response)

            # Audit successful request
            await self.security_service.audit_request(
                request=request,
                response_status=response.status_code,
                duration=time.time() - start_time
            )

            return response

        except Exception as e:
            # Audit failed request
            if self.security_service:
                await self.security_service.audit_request(
                    request=request,
                    response_status=500,
                    duration=time.time() - start_time,
                    error=str(e)
                )

            logger.error(f"Security error: {str(e)}")
            if isinstance(e, SecurityError):
                raise
            raise SecurityError(detail="Security check failed")
