"""Security-related constants."""
from typing import Dict, Final, Set

# Security Headers
SECURITY_HEADERS: Final[Dict[str, str]] = {
    "X-Frame-Options": "DENY",
    "X-Content-Type-Options": "nosniff",
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": (
        "accelerometer=(), camera=(), geolocation=(), "
        "magnetometer=(), microphone=(), payment=(), usb=()"
    )
}

# Request Tracking
REQUEST_ID_HEADER: Final[str] = "X-Request-ID"
CORRELATION_ID_HEADER: Final[str] = "X-Correlation-ID"

# CSRF Protection
CSRF_METHODS: Final[Set[str]] = {"POST", "PUT", "DELETE", "PATCH"}
CSRF_SAFE_METHODS: Final[Set[str]] = {"GET", "HEAD", "OPTIONS"}

# Rate Limiting
DEFAULT_RATE_LIMIT: Final[int] = 60  # requests per minute
DEFAULT_BURST_SIZE: Final[int] = 100

# Token Settings
TOKEN_EXPIRY_BUFFER: Final[int] = 300  # seconds
REFRESH_TOKEN_LENGTH: Final[int] = 64
ACCESS_TOKEN_LENGTH: Final[int] = 32

# Security Event Settings
MAX_LOGIN_ATTEMPTS: Final[int] = 5
LOGIN_ATTEMPT_WINDOW: Final[int] = 15  # minutes
SUSPICIOUS_IP_THRESHOLD: Final[int] = 10
EVENT_RETENTION_DAYS: Final[int] = 90

# Password requirements
MIN_PASSWORD_LENGTH: Final[int] = 12
PASSWORD_SPECIAL_CHARS: Final[str] = "!@#$%^&*(),.?\":{}|<>"

# Token types
TOKEN_TYPE_ACCESS: Final[str] = "access"
TOKEN_TYPE_REFRESH: Final[str] = "refresh"
TOKEN_TYPE_RESET: Final[str] = "reset"
TOKEN_TYPE_VERIFY: Final[str] = "verify"

# CSP Directives
CSP_DIRECTIVES: Final[dict] = {
    'default-src': "'self'",
    'script-src': "'self' 'unsafe-inline'",
    'style-src': "'self' 'unsafe-inline'",
    'img-src': "'self' data: https:",
    'font-src': "'self'",
    'connect-src': "'self'",
    'frame-ancestors': "'none'",
    'form-action': "'self'",
    'base-uri': "'self'",
    'object-src': "'none'",
    'upgrade-insecure-requests': ''
}
