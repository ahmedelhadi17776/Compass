"""Security utilities."""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from typing import Dict, Any
from src.core.config import settings
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)

class SecurityHeaders:
    """Security headers manager."""
    
    @staticmethod
    def get_security_headers() -> Dict[str, str]:
        """Get security headers configuration."""
        return {
            # Prevent clickjacking attacks
            "X-Frame-Options": "DENY",
            
            # Prevent MIME type sniffing
            "X-Content-Type-Options": "nosniff",
            
            # Enable browser XSS filtering
            "X-XSS-Protection": "1; mode=block",
            
            # Enable HSTS
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
            
            # Set CSP headers
            "Content-Security-Policy": (
                "default-src 'self'; "
                "img-src 'self' data: https:; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https:; "
                "style-src 'self' 'unsafe-inline' https:; "
                "font-src 'self' data: https:; "
                "connect-src 'self' https:; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self';"
            ),
            
            # Prevent browsers from performing MIME sniffing
            "X-Permitted-Cross-Domain-Policies": "none",
            
            # Control browser features
            "Permissions-Policy": (
                "accelerometer=(), "
                "camera=(), "
                "geolocation=(), "
                "gyroscope=(), "
                "magnetometer=(), "
                "microphone=(), "
                "payment=(), "
                "usb=()"
            ),
            
            # Enable browser DNS prefetching
            "X-DNS-Prefetch-Control": "on",
            
            # Disable client-side caching for authenticated pages
            "Cache-Control": "no-store, max-age=0",
            
            # Prevent pages from loading when XSS is detected
            "X-XSS-Protection": "1; mode=block"
        }
    
    @staticmethod
    def apply_security_headers(response: Response) -> None:
        """Apply security headers to response."""
        headers = SecurityHeaders.get_security_headers()
        
        # Only apply HSTS in production
        if not settings.DEBUG:
            headers["Strict-Transport-Security"] = (
                "max-age=31536000; "
                "includeSubDomains; "
                "preload"
            )
        
        # Apply headers
        for header, value in headers.items():
            response.headers[header] = value

class SecurityMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to responses."""
    
    async def dispatch(self, request: Request, call_next: Any) -> Response:
        """Add security headers to response."""
        response = await call_next(request)
        SecurityHeaders.apply_security_headers(response)
        return response
