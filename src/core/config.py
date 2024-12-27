"""Core configuration settings."""
from pydantic_settings import BaseSettings
from typing import List, Dict, Any, Set
import os


class Settings(BaseSettings):
    """Application settings."""
    # Project info
    PROJECT_NAME: str = "AIWA Platform"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    DESCRIPTION: str = "AI Workflow Automation Platform"

    # Security Settings
    SECURITY_MIDDLEWARE_CONFIG: Dict[str, Any] = {
        "allowed_hosts": ["*"],  # Override in production
        "force_https": True,
        "hsts_seconds": 31536000,
        "include_subdomains": True,
        "preload": True
    }

    # Authentication Settings
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_RESET_TOKEN_EXPIRE_HOURS: int = 24

    # Password Policy
    MIN_PASSWORD_LENGTH: int = 12
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_DIGITS: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = True
    PASSWORD_HISTORY_SIZE: int = 5

    # Session Settings
    SESSION_COOKIE_NAME: str = "session"
    SESSION_EXPIRE_MINUTES: int = 60
    SESSION_EXPIRE_DAYS: int = 30
    MAX_SESSIONS_PER_USER: int = 5
    SESSION_REFRESH_MINUTES: int = 15
    SESSION_CLEANUP_INTERVAL_MINUTES: int = 60

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_BURST_SIZE: int = 100
    MAX_FAILED_LOGIN_ATTEMPTS: int = 5
    LOGIN_BLOCK_DURATION: int = 300  # 5 minutes

    # CORS Settings
    CORS_ORIGINS: List[str] = ["*"]  # Override in production
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]

    # CSRF Settings
    CSRF_COOKIE_NAME: str = "csrf_token"
    CSRF_HEADER_NAME: str = "X-CSRF-Token"
    CSRF_SAFE_METHODS: Set[str] = {"GET", "HEAD", "OPTIONS"}
    CSRF_TOKEN_EXPIRY: int = 3600  # 1 hour

    # Security Headers
    SECURITY_HEADERS_HSTS_AGE: int = 31536000  # 1 year
    SECURITY_HEADERS_INCLUDE_SUBDOMAINS: bool = True
    SECURITY_HEADERS_PRELOAD: bool = True

    # Audit Logging
    AUDIT_LOG_ENABLED: bool = True
    AUDIT_LOG_RETENTION_DAYS: int = 90

    # Security Events
    SECURITY_EVENT_RETENTION_DAYS: int = 90
    MAX_FAILED_LOGIN_ATTEMPTS: int = 5
    LOGIN_BLOCK_DURATION: int = 300  # 5 minutes

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
