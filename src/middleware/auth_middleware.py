"""Authentication middleware for FastAPI application."""
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import time
from typing import Dict, Tuple, Optional, Set
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from src.core.config import settings

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class RequestTracker:
    """Track request timestamps and metadata."""
    timestamps: list[float] = field(default_factory=list)
    failed_attempts: int = 0
    last_failed_attempt: Optional[float] = None
    blocked_until: Optional[float] = None

class RateLimiter:
    """Rate limiting implementation with IP tracking."""
    
    def __init__(
        self,
        requests_per_minute: int = settings.RATE_LIMIT_REQUESTS_PER_MINUTE,
        max_failed_attempts: int = settings.MAX_FAILED_LOGIN_ATTEMPTS,
        block_duration: int = settings.LOGIN_BLOCK_DURATION
    ):
        self.requests_per_minute = requests_per_minute
        self.max_failed_attempts = max_failed_attempts
        self.block_duration = block_duration  # in seconds
        self.requests: Dict[str, RequestTracker] = {}
        self.blacklisted_ips: Set[str] = set()
    
    def _clean_old_requests(self, ip: str, now: float) -> None:
        """Remove requests older than 1 minute."""
        minute_ago = now - 60
        tracker = self.requests[ip]
        tracker.timestamps = [t for t in tracker.timestamps if t > minute_ago]
        
        # Reset failed attempts if block duration has passed
        if (tracker.blocked_until and now > tracker.blocked_until):
            tracker.failed_attempts = 0
            tracker.blocked_until = None
    
    def is_rate_limited(self, ip: str) -> Tuple[bool, float, str]:
        """
        Check if request should be rate limited.
        
        Returns:
            Tuple[bool, float, str]: (is_limited, wait_time, message)
        """
        now = time.time()
        
        # Check if IP is blacklisted
        if ip in self.blacklisted_ips:
            return True, float('inf'), "IP address has been blocked due to suspicious activity"
        
        # Initialize tracker if not exists
        if ip not in self.requests:
            self.requests[ip] = RequestTracker()
        
        tracker = self.requests[ip]
        self._clean_old_requests(ip, now)
        
        # Check if IP is temporarily blocked
        if tracker.blocked_until:
            if now < tracker.blocked_until:
                wait_time = tracker.blocked_until - now
                return True, wait_time, f"Too many failed attempts. Try again in {wait_time:.0f} seconds"
        
        # Check rate limit
        if len(tracker.timestamps) >= self.requests_per_minute:
            wait_time = 60 - (now - tracker.timestamps[0])
            return True, wait_time, f"Rate limit exceeded. Try again in {wait_time:.0f} seconds"
        
        tracker.timestamps.append(now)
        return False, 0, ""
    
    def record_failed_attempt(self, ip: str) -> Tuple[bool, float, str]:
        """
        Record a failed authentication attempt.
        
        Returns:
            Tuple[bool, float, str]: (is_blocked, block_duration, message)
        """
        now = time.time()
        tracker = self.requests.get(ip)
        if not tracker:
            tracker = RequestTracker()
            self.requests[ip] = tracker
        
        tracker.failed_attempts += 1
        tracker.last_failed_attempt = now
        
        if tracker.failed_attempts >= self.max_failed_attempts:
            tracker.blocked_until = now + self.block_duration
            logger.warning(f"IP {ip} blocked for {self.block_duration} seconds due to too many failed attempts")
            return True, self.block_duration, f"Account locked. Try again in {self.block_duration} seconds"
        
        return False, 0, f"Failed attempt {tracker.failed_attempts}/{self.max_failed_attempts}"
    
    def blacklist_ip(self, ip: str) -> None:
        """Permanently blacklist an IP address."""
        self.blacklisted_ips.add(ip)
        logger.warning(f"IP {ip} has been blacklisted")
    
    def reset_failed_attempts(self, ip: str) -> None:
        """Reset failed attempts counter after successful authentication."""
        if ip in self.requests:
            self.requests[ip].failed_attempts = 0
            self.requests[ip].blocked_until = None

class AuthMiddleware:
    """Authentication middleware with rate limiting and request tracking."""
    
    def __init__(self):
        self.rate_limiter = RateLimiter()
    
    async def __call__(self, request: Request, call_next):
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Check if the request is for an auth endpoint
        if "/api/auth/" in request.url.path:
            # Rate limiting check
            is_limited, wait_time, message = self.rate_limiter.is_rate_limited(client_ip)
            if is_limited:
                logger.warning(f"Rate limit exceeded for IP: {client_ip}")
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"detail": message}
                )
            
            # Log auth attempt
            logger.info(
                f"Auth attempt from IP: {client_ip}, "
                f"Path: {request.url.path}, "
                f"Method: {request.method}"
            )
            
            # Record start time
            start_time = time.time()
            
            # Process request
            response = await call_next(request)
            
            # Handle failed authentication
            if response.status_code in {401, 403}:
                is_blocked, block_time, message = self.rate_limiter.record_failed_attempt(client_ip)
                if is_blocked:
                    return JSONResponse(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        content={"detail": message}
                    )
            elif response.status_code == 200 and request.url.path.endswith("/login"):
                # Reset failed attempts on successful login
                self.rate_limiter.reset_failed_attempts(client_ip)
            
            # Log response time and status
            process_time = time.time() - start_time
            logger.info(
                f"Auth request completed - "
                f"IP: {client_ip}, "
                f"Path: {request.url.path}, "
                f"Method: {request.method}, "
                f"Status: {response.status_code}, "
                f"Time: {process_time:.3f}s"
            )
            
            return response
        
        return await call_next(request)

def setup_auth_middleware(app):
    """Add authentication middleware to FastAPI app."""
    app.middleware("http")(AuthMiddleware())
