"""Rate limiting module."""
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional
import time
from dataclasses import dataclass
from .exceptions import RateLimitExceeded


@dataclass
class RateLimit:
    """Rate limit configuration."""
    requests: int
    window: int  # seconds


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
