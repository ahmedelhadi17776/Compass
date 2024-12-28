"""Security event handling."""
from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel


class SecurityEventType(str, Enum):
    """Security event types."""
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    PASSWORD_CHANGED = "password_changed"
    PASSWORD_RESET = "password_reset"
    ACCESS_DENIED = "access_denied"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    TOKEN_REVOKED = "token_revoked"
    USER_CREATED = "user_created"
    USER_DELETED = "user_deleted"
    USER_UPDATED = "user_updated"
    TASK_CREATED = "task_created"
    TASK_UPDATED = "task_updated"
    TASK_DELETED = "task_deleted"
    ERROR = "error"


class SecurityEvent(BaseModel):
    """Security event model."""
    event_type: SecurityEventType
    timestamp: datetime
    description: str
    severity: str
    metadata: Dict[str, Any]
    user_id: Optional[int] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
