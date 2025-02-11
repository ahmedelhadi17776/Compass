"""Security context middleware."""
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional
import logging
from Backend.core.security.context import SecurityContext
from Backend.core.security import TokenManager, EncryptionService
from Backend.core.security.constants import REQUEST_ID_HEADER, CORRELATION_ID_HEADER
from Backend.core.security.exceptions import SecurityConfigError

logger = logging.getLogger(__name__)


class SecurityContextMiddleware(BaseHTTPMiddleware):
    """Middleware for setting up security context."""

    def __init__(
        self,
        app,
        token_manager: Optional[TokenManager] = None,
        encryption_service: Optional[EncryptionService] = None
    ):
        super().__init__(app)
        self.token_manager = token_manager or TokenManager()
        self.encryption_service = encryption_service or EncryptionService()

    async def dispatch(self, request: Request, call_next) -> Response:
        # Create security context
        context = SecurityContext.create(
            token_manager=self.token_manager,
            encryption_service=self.encryption_service,
            client_ip=request.client.host,
            path=request.url.path,
            method=request.method,
            user_agent=request.headers.get("user-agent"),
            correlation_id=request.headers.get(CORRELATION_ID_HEADER)
        )

        # Add context to request state
        request.state.security_context = context
        request.state.request_id = context.request_id

        # Process request
        response = await call_next(request)

        # Add tracking headers
        response.headers[REQUEST_ID_HEADER] = context.request_id
        if context.correlation_id:
            response.headers[CORRELATION_ID_HEADER] = context.correlation_id

        return response
