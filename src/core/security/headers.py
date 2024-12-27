"""Security headers service."""
from typing import Dict, Optional
from fastapi import Response
from .constants import SECURITY_HEADERS, CSP_DIRECTIVES


class SecurityHeadersService:
    """Service for managing security headers."""

    @staticmethod
    def apply_security_headers(
        response: Response,
        custom_csp: Optional[Dict[str, str]] = None,
        custom_headers: Optional[Dict[str, str]] = None
    ) -> None:
        """Apply security headers to response."""
        headers = SECURITY_HEADERS.copy()

        # Build CSP header
        csp_directives = CSP_DIRECTIVES.copy()
        if custom_csp:
            csp_directives.update(custom_csp)
        headers['Content-Security-Policy'] = SecurityHeadersService._build_csp_header(
            csp_directives)

        # Add custom headers
        if custom_headers:
            headers.update(custom_headers)

        # Apply all headers
        for key, value in headers.items():
            response.headers[key] = value

    @staticmethod
    def _build_csp_header(directives: Dict[str, str]) -> str:
        """Build Content Security Policy header value."""
        return '; '.join(f"{k} {v}".strip() for k, v in directives.items())

    @staticmethod
    def add_security_headers(headers: Dict[str, str]) -> Dict[str, str]:
        """Add security headers to existing headers dict."""
        secure_headers = SECURITY_HEADERS.copy()
        secure_headers['Content-Security-Policy'] = SecurityHeadersService._build_csp_header(
            CSP_DIRECTIVES)
        headers.update(secure_headers)
        return headers
