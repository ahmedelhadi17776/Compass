"""CSRF protection middleware."""
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_403_FORBIDDEN
import secrets
import time
from typing import Optional, Set
import logging

from src.core.security.logging import SecurityLogger

logger = logging.getLogger(__name__)


class CSRFMiddleware(BaseHTTPMiddleware):
    """CSRF protection middleware."""

    def __init__(
        self,
        app,
        secret_key: str,
        cookie_name: str = "csrf_token",
        header_name: str = "X-CSRF-Token",
        safe_methods: Set[str] = {"GET", "HEAD", "OPTIONS"},
        token_expiry: int = 3600  # 1 hour
    ):
        super().__init__(app)
        self.secret_key = secret_key
        self.cookie_name = cookie_name
        self.header_name = header_name
        self.safe_methods = safe_methods
        self.token_expiry = token_expiry

    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip CSRF check for safe methods
        if request.method in self.safe_methods:
            response = await call_next(request)
            self._set_csrf_cookie(response)
            return response

        # Verify CSRF token
        cookie_token = request.cookies.get(self.cookie_name)
        header_token = request.headers.get(self.header_name)

        if not self._verify_csrf_token(cookie_token, header_token):
            SecurityLogger.warning(
                "CSRF token validation failed",
                context=request.state.security_context
            )
            return Response(
                content={"detail": "CSRF token validation failed"},
                status_code=HTTP_403_FORBIDDEN
            )

        response = await call_next(request)
        self._set_csrf_cookie(response)
        return response

    def _generate_token(self) -> str:
        """Generate a new CSRF token."""
        return secrets.token_urlsafe(32)

    def _set_csrf_cookie(self, response: Response) -> None:
        """Set CSRF token cookie."""
        token = self._generate_token()
        response.set_cookie(
            key=self.cookie_name,
            value=token,
            httponly=True,
            samesite="strict",
            secure=True,
            max_age=self.token_expiry
        )

    def _verify_csrf_token(
        self,
        cookie_token: Optional[str],
        header_token: Optional[str]
    ) -> bool:
        """Verify CSRF token from cookie matches header."""
        if not cookie_token or not header_token:
            return False
        return secrets.compare_digest(cookie_token, header_token)
