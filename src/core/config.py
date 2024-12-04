"""Core configuration settings."""
from pydantic_settings import BaseSettings
from typing import List
import os
from pathlib import Path

class Settings(BaseSettings):
    """Application settings."""
    # Project info
    PROJECT_NAME: str = "AIWA Platform"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    DESCRIPTION: str = "AI Workflow Automation Platform"
    
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4
    LOG_LEVEL: str = "INFO"
    
    # API settings
    API_V1_STR: str = "/api"
    
    # Security
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ACCESS_TOKEN_EXPIRE_DAYS: int = 1
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 60
    MAX_FAILED_LOGIN_ATTEMPTS: int = 5
    LOGIN_BLOCK_DURATION: int = 300  # 5 minutes in seconds
    
    # Password Policy
    MIN_PASSWORD_LENGTH: int = 8
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_DIGITS: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = True
    PASSWORD_HISTORY_SIZE: int = 5
    
    # Session
    SESSION_EXPIRE_MINUTES: int = 60
    SESSION_EXPIRE_DAYS: int = 30  # Default session expiration in days
    MAX_SESSIONS_PER_USER: int = 5
    SESSION_REFRESH_MINUTES: int = 15  # Refresh session if activity within this window
    SESSION_CLEANUP_INTERVAL_MINUTES: int = 60  # How often to cleanup expired sessions
    
    # CORS
    CORS_ORIGINS: List[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/aiwa_db"
    )
    SQL_ECHO: bool = False  # Whether to log SQL queries
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    
    # Email
    SMTP_TLS: bool = True
    SMTP_PORT: int = 587
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    EMAILS_FROM_EMAIL: str = os.getenv("EMAILS_FROM_EMAIL", "noreply@aiwa.com")
    EMAILS_FROM_NAME: str = os.getenv("EMAILS_FROM_NAME", "AIWA Platform")
    
    # Email Verification
    EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS: int = 48
    REQUIRE_EMAIL_VERIFICATION: bool = True
    
    # Password Reset
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 30
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB in bytes
    ALLOWED_UPLOAD_EXTENSIONS: List[str] = [".pdf", ".doc", ".docx", ".txt"]
    UPLOAD_DIR: str = "uploads"
    
    # Security Headers
    SECURITY_HEADERS: dict = {
        "X-Frame-Options": "DENY",
        "X-Content-Type-Options": "nosniff",
        "X-XSS-Protection": "1; mode=block",
        "Content-Security-Policy": (
            "default-src 'self'; "
            "img-src 'self' data:; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline';"
        ),
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Referrer-Policy": "strict-origin-when-cross-origin"
    }
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
