"""Authentication service package."""
from .auth_service import AuthService

# Export AuthService as AuthenticationService for backward compatibility
AuthenticationService = AuthService

__all__ = ['AuthService', 'AuthenticationService']