"""Security-related exceptions."""
from fastapi import HTTPException, status


class SecurityError(HTTPException):
    """Base class for security errors."""

    def __init__(self, detail: str = None, headers: dict = None):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail or "Security error",
            headers=headers or {"WWW-Authenticate": "Bearer"}
        )


class AuthError(SecurityError):
    """Base class for authentication errors."""

    def __init__(self, detail: str = None, headers: dict = None):
        super().__init__(
            detail=detail or "Authentication failed",
            headers=headers or {"WWW-Authenticate": "Bearer"}
        )


class InvalidTokenError(AuthError):
    """Raised when a token is invalid."""

    def __init__(self):
        super().__init__(detail="Invalid token")


class ExpiredTokenError(AuthError):
    """Raised when a token has expired."""

    def __init__(self):
        super().__init__(detail="Token has expired")


class TokenBlacklistedError(AuthError):
    """Raised when a blacklisted token is used."""

    def __init__(self):
        super().__init__(detail="Token has been blacklisted")


class InvalidCredentialsError(AuthError):
    """Raised when credentials are invalid."""

    def __init__(self):
        super().__init__(detail="Invalid credentials")


class SecurityConfigError(SecurityError):
    """Raised when there's a security configuration error."""

    def __init__(self, detail: str = None):
        super().__init__(
            detail=detail or "Security configuration error",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class RateLimitExceededError(SecurityError):
    """Raised when rate limit is exceeded."""

    def __init__(self):
        super().__init__(
            detail="Rate limit exceeded",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS
        )


class AccessDeniedError(SecurityError):
    """Raised when access is denied."""

    def __init__(self, detail: str = None):
        super().__init__(
            detail=detail or "Access denied",
            status_code=status.HTTP_403_FORBIDDEN
        )


class TaskNotFoundError(SecurityError):
    """Raised when a task is not found."""

    def __init__(self, task_id: int):
        super().__init__(
            detail=f"Task not found: {task_id}",
            status_code=status.HTTP_404_NOT_FOUND
        )
