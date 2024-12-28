"""Rate limiting configuration and utilities."""
from dataclasses import dataclass
from typing import Optional
from src.core.security.constants import (
    DEFAULT_RATE_LIMIT,
    DEFAULT_BURST_SIZE
)


@dataclass
class RateLimitConfig:
    """Rate limit configuration."""
    requests_per_minute: int = DEFAULT_RATE_LIMIT
    burst_size: int = DEFAULT_BURST_SIZE

    def validate(self) -> None:
        """Validate rate limit configuration."""
        if self.requests_per_minute < 1:
            raise ValueError("requests_per_minute must be positive")
        if self.burst_size < self.requests_per_minute:
            raise ValueError(
                "burst_size must be greater than requests_per_minute")


class RateLimitKey:
    """Rate limit key generator."""

    @staticmethod
    def for_ip(ip: str) -> str:
        """Generate rate limit key for IP."""
        return f"rate_limit:ip:{ip}"

    @staticmethod
    def for_user(user_id: int) -> str:
        """Generate rate limit key for user."""
        return f"rate_limit:user:{user_id}"

    @staticmethod
    def for_endpoint(path: str, method: str) -> str:
        """Generate rate limit key for endpoint."""
        return f"rate_limit:endpoint:{method}:{path}"


class RateLimiter:
    """In-memory rate limiter."""

    def __init__(self):
        self._requests: Dict[str, list[float]] = {}

    def is_allowed(self, key: str, limit: RateLimit) -> Tuple[bool, Optional[float]]:
        """Check if request is allowed and return retry-after if not."""
        now = time.time()

        # Clean old requests
        self._requests[key] = [
            req_time for req_time in self._requests.get(key, [])
            if now - req_time < limit.window
        ]

        # Check limit
        if len(self._requests[key]) >= limit.requests:
            oldest_request = self._requests[key][0]
            retry_after = limit.window - (now - oldest_request)
            return False, max(0, retry_after)

        # Add new request
        self._requests[key] = self._requests.get(key, []) + [now]
        return True, None

    def clear(self, key: str):
        """Clear rate limit data for key."""
        self._requests.pop(key, None)
