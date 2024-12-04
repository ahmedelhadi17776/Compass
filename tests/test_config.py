"""Test configuration module."""
from unittest.mock import Mock

# Mock email service configuration
class MockEmailService:
    def __init__(self):
        pass
    
    def send_email(self, *args, **kwargs):
        return True
    
    def send_verification_email(self, *args, **kwargs):
        return True
    
    def send_password_reset_email(self, *args, **kwargs):
        return True

# Create mock instance
mock_email_service = MockEmailService()

# Override environment variables for testing
test_settings = {
    "EMAIL_ENABLED": True,
    "EMAIL_HOST": "localhost",
    "EMAIL_PORT": 1025,
    "EMAIL_USERNAME": "test",
    "EMAIL_PASSWORD": "test",
    "EMAIL_FROM": "test@example.com",
    "EMAIL_FROM_NAME": "Test System",
    "JWT_SECRET_KEY": "test_secret_key_123",
    "JWT_ALGORITHM": "HS256",
    "ACCESS_TOKEN_EXPIRE_MINUTES": 30,
    "REFRESH_TOKEN_EXPIRE_DAYS": 7,
    "RATE_LIMIT_REQUESTS_PER_MINUTE": 60,
    "MAX_FAILED_LOGIN_ATTEMPTS": 5,
    "LOGIN_BLOCK_DURATION": 300,
    "SESSION_CLEANUP_INTERVAL_HOURS": 24,
    "ENVIRONMENT": "test"
}
