"""Security audit middleware."""
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from typing import Optional

from src.core.security.logging import SecurityLogger
from src.data.database.models.security_log import SecurityAuditLog
from src.data.database.session import get_db

import time

logger = logging.getLogger(__name__)


class SecurityAuditMiddleware(BaseHTTPMiddleware):
    """Middleware for security audit logging."""

    async def dispatch(self, request: Request, call_next) -> Response:
        # Get security context
        context = request.state.security_context

        # Start timer
        start_time = time.time()

        try:
            # Process request
            response = await call_next(request)

            # Log successful requests
            await self._log_request(
                request=request,
                response=response,
                context=context,
                duration=time.time() - start_time
            )

            return response

        except Exception as e:
            # Log failed requests
            await self._log_request(
                request=request,
                error=str(e),
                context=context,
                duration=time.time() - start_time
            )
            raise

    async def _log_request(
        self,
        request: Request,
        response: Optional[Response] = None,
        error: Optional[str] = None,
        context: Optional[dict] = None,
        duration: Optional[float] = None
    ) -> None:
        """Log request details to security audit log."""
        try:
            # Get database session
            db: AsyncSession = await get_db()

            # Create audit log entry
            log_entry = SecurityAuditLog(
                event_type="request",
                user_id=getattr(request.state, "user_id", None),
                ip_address=request.client.host,
                user_agent=request.headers.get("user-agent"),
                request_path=request.url.path,
                request_method=request.method,
                details={
                    "status_code": getattr(response, "status_code", None),
                    "error": error,
                    "duration": f"{duration:.3f}s" if duration else None,
                    "headers": dict(request.headers),
                    "query_params": dict(request.query_params),
                    "context": context
                }
            )

            db.add(log_entry)
            await db.commit()

        except Exception as e:
            logger.error(f"Failed to create audit log: {str(e)}")
