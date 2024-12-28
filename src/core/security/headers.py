"""Security headers service."""
from fastapi import Response
from src.core.security.constants import SECURITY_HEADERS


class SecurityHeadersService:
    """Service for managing security headers."""

    @staticmethod
    def apply_security_headers(response: Response) -> None:
        """Apply security headers to response."""
        for header, value in SECURITY_HEADERS.items():
            response.headers[header] = value

    @staticmethod
    def get_cors_headers(allowed_origins: list[str]) -> dict:
        """Get CORS headers configuration."""
        return {
            "allow_origins": allowed_origins,
            "allow_credentials": True,
            "allow_methods": ["*"],
            "allow_headers": ["*"],
        }

    @staticmethod
    def get_csp_header() -> str:
        """Get Content Security Policy header value."""
        return "; ".join([
            "default-src 'self'",
            "img-src 'self' data: https:",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
            "style-src 'self' 'unsafe-inline'",
            "connect-src 'self'",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'"
        ])
