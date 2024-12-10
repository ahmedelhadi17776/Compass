"""Test configuration module."""
from unittest.mock import Mock

# Mock email service configuration
class MockEmailService:
    async def send_email(self, *args, **kwargs):
        return True

    async def send_password_reset(self, *args, **kwargs):
        return True

    async def send_verification_email(self, *args, **kwargs):
        return True

    async def send_task_notification(self, *args, **kwargs):
        return True

    async def send_workflow_notification(self, *args, **kwargs):
        return True

# Create mock instance
mock_email_service = MockEmailService()

# Override environment variables for testing
test_settings = {
    # Auth settings
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
    
    # Task settings
    "MAX_TASK_ATTACHMENTS": 10,
    "MAX_ATTACHMENT_SIZE_MB": 50,
    "ALLOWED_ATTACHMENT_TYPES": "pdf,doc,docx,txt,jpg,png",
    "TASK_DUE_DATE_REMINDER_DAYS": [1, 3, 7],
    "TASK_OVERDUE_CHECK_INTERVAL_HOURS": 1,
    
    # Workflow settings
    "MAX_WORKFLOW_STEPS": 20,
    "WORKFLOW_STEP_TIMEOUT_MINUTES": 60,
    "MAX_STEP_RETRIES": 3,
    "WORKFLOW_CHECK_INTERVAL_MINUTES": 5,
    "AUTO_ADVANCE_WORKFLOW": True,
    
    # General settings
    "ENVIRONMENT": "test",
    "DEBUG": True,
    "API_V1_PREFIX": "/api/v1",
    "APP_NAME": "AIWA Test",
    "APP_VERSION": "1.0.0"
}
