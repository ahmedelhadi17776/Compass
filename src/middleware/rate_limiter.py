"""Rate limiter middleware."""
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import time
import logging
from src.core.security.rate_limit import RateLimitConfig
from src.core.security.exceptions import RateLimitExceededError

logger = logging.getLogger(__name__)


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting requests."""

    def __init__(self, app, config: RateLimitConfig):
        super().__init__(app)
        self.config = config
        self.requests = {}  # IP -> list of timestamps

    async def dispatch(self, request: Request, call_next) -> Response:
        client_ip = request.client.host
        now = time.time()

        # Clean old requests
        if client_ip in self.requests:
            self.requests[client_ip] = [
                ts for ts in self.requests[client_ip]
                if now - ts < 60  # Keep last minute
            ]

        # Check rate limit
        if self._is_rate_limited(client_ip, now):
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            raise RateLimitExceededError()

        # Add current request
        if client_ip not in self.requests:
            self.requests[client_ip] = []
        self.requests[client_ip].append(now)

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        self._add_rate_limit_headers(response, client_ip)

        return response

    def _is_rate_limited(self, client_ip: str, now: float) -> bool:
        """Check if request should be rate limited."""
        if client_ip not in self.requests:
            return False

        recent_requests = len([
            ts for ts in self.requests[client_ip]
            if now - ts < 60
        ])

        return recent_requests >= self.config.requests_per_minute

    def _add_rate_limit_headers(self, response: Response, client_ip: str):
        """Add rate limit headers to response."""
        recent_requests = len(self.requests.get(client_ip, []))
        remaining = max(0, self.config.requests_per_minute - recent_requests)

        response.headers["X-RateLimit-Limit"] = str(
            self.config.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(time.time() + 60))
