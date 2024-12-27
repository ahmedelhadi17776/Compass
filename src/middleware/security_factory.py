"""Security middleware factory."""
from fastapi import FastAPI
from typing import Optional

from src.core.security import TokenManager, EncryptionService
from src.core.security.rate_limit import RateLimitConfig
from .security_context import SecurityContextMiddleware
from .rate_limiter import RateLimiterMiddleware
from .security import SecurityMiddleware


def setup_security_middleware(
    app: FastAPI,
    token_manager: Optional[TokenManager] = None,
    encryption_service: Optional[EncryptionService] = None,
    rate_limit_config: Optional[RateLimitConfig] = None
) -> None:
    """Set up all security-related middleware."""

    # Add security context middleware
    app.add_middleware(
        SecurityContextMiddleware,
        token_manager=token_manager,
        encryption_service=encryption_service
    )

    # Add rate limiter middleware if config provided
    if rate_limit_config:
        app.add_middleware(
            RateLimiterMiddleware,
            config=rate_limit_config
        )

    # Add general security middleware
    app.add_middleware(SecurityMiddleware)
