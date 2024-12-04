"""Custom exceptions for the application."""
from fastapi import HTTPException, status

class AuthError(HTTPException):
    """Base class for authentication errors."""
    def __init__(self, detail: str = None, headers: dict = None):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail or "Authentication failed",
            headers=headers or {"WWW-Authenticate": "Bearer"}
        )

class PermissionError(HTTPException):
    """Base class for permission errors."""
    def __init__(self, detail: str = None):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail or "Permission denied"
        )

class ResourceNotFoundError(HTTPException):
    """Base class for resource not found errors."""
    def __init__(self, detail: str = None):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail or "Resource not found"
        )

class ValidationError(HTTPException):
    """Base class for validation errors."""
    def __init__(self, detail: str = None):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail or "Validation error"
        )
