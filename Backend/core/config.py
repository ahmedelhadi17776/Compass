from pydantic_settings import BaseSettings
from typing import List, Optional
from pydantic import validator, AnyHttpUrl, EmailStr
import json
import os


class Settings(BaseSettings):
    # Database settings
    DB_USER: str = "ahmed"
    DB_PASSWORD: str = "0502747598"
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "compass"
    DATABASE_URL: str = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

    # JWT settings
    JWT_SECRET_KEY: str = "a82552a2c8133eddce94cc781f716cdcb911d065528783a8a75256aff6731886"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # App settings
    APP_NAME: str = "COMPASS"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # Test settings
    TESTING: bool = False
    TEST_DATABASE_URL: str = "postgresql+asyncpg://postgres:0502747598@localhost:5432/compass_test"
    TEST_REDIS_URL: str = "redis://localhost:6379/1"  # Use different DB for testing

    # Database initialization settings
    DB_INIT_MODE: str = "dev"
    CREATE_ADMIN: bool = True
    DB_DROP_TABLES: bool = True

    # Admin credentials
    ADMIN_EMAIL: EmailStr = "admin@aiwa.com"
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "aiwa_admin_2024!"

    # API Configuration
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: List[AnyHttpUrl] = []

    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Redis settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    REDIS_URL: str = "redis://localhost:6379/0"

    # Celery settings
    CELERY_BROKER_URL: str = REDIS_URL
    CELERY_RESULT_BACKEND: str = REDIS_URL
    CELERY_TASK_ALWAYS_EAGER: bool = False
    CELERY_TASK_EAGER_PROPAGATES: bool = False  # Added for testing
    CELERY_TASK_STORE_EAGER_RESULT: bool = False  # Added for testing
    CELERY_TASK_SERIALIZER: str = "json"
    CELERY_RESULT_SERIALIZER: str = "json"
    CELERY_ACCEPT_CONTENT: List[str] = ["json"]
    CELERY_TIMEZONE: str = "UTC"
    CELERY_ENABLE_UTC: bool = True
    CELERY_TASK_SOFT_TIME_LIMIT: int = 60 * 30  # 30 minutes
    CELERY_WORKER_PREFETCH_MULTIPLIER: int = 1
    CELERY_TASK_ACKS_LATE: bool = True
    CELERY_TASK_REJECT_ON_WORKER_LOST: bool = True
    CELERY_TASK_DEFAULT_QUEUE: str = "default"
    CELERY_TASK_DEFAULT_EXCHANGE: str = "default"
    CELERY_TASK_DEFAULT_ROUTING_KEY: str = "default"
    CELERY_TASK_CREATE_MISSING_QUEUES: bool = True
    CELERY_RESULT_EXPIRES: int = 3600  # Results expire in 1 hour
    CELERY_TASK_TRACK_STARTED: bool = True
    CELERY_TASK_TIME_LIMIT: int = 3600  # 1 hour
    CELERY_TASK_SEND_SENT_EVENT: bool = True
    CELERY_TASK_STORE_ERRORS_EVEN_IF_IGNORED: bool = True

    @validator("DATABASE_URL", pre=True)
    def assemble_db_url(cls, v: Optional[str], values: dict) -> str:
        if os.getenv("TESTING") == "True":
            return "sqlite+aiosqlite:///./test.db"
        if v:
            # Convert standard postgres:// to postgresql+asyncpg://
            if v.startswith("postgres://"):
                v = v.replace("postgres://", "postgresql+asyncpg://", 1)
            elif v.startswith("postgresql://"):
                v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
            return v
        return f"postgresql+asyncpg://{values.get('DB_USER')}:{values.get('DB_PASSWORD')}@{values.get('DB_HOST')}:{values.get('DB_PORT')}/{values.get('DB_NAME')}"

    @validator("CORS_ORIGINS", pre=True)
    def parse_cors_origins(cls, v: str | List[str]) -> List[str]:
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [v]
        return v

    @validator("REDIS_URL", pre=True)
    def assemble_redis_url(cls, v: Optional[str], values: dict) -> str:
        if v:
            return v
        password = values.get('REDIS_PASSWORD')
        auth = f":{password}@" if password else ""
        return f"redis://{auth}{values.get('REDIS_HOST', 'localhost')}:{values.get('REDIS_PORT', 6379)}/{values.get('REDIS_DB', 0)}"

    @validator("CELERY_BROKER_URL", "CELERY_RESULT_BACKEND", pre=True)
    def set_celery_urls(cls, v: Optional[str], values: dict) -> str:
        if v:
            return v
        return values.get("REDIS_URL", "redis://localhost:6379/0")

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"
        env_file_encoding = 'utf-8'


# Initialize settings with fallback values for testing
test_values = {
    "DB_USER": "postgres",
    "DB_PASSWORD": "0502747598",
    "DB_HOST": "localhost",
    "DB_PORT": 5432,
    "DB_NAME": "compass_test",
    "JWT_SECRET_KEY": "test_secret_key",
    "APP_NAME": "COMPASS_TEST",
    "APP_VERSION": "test",
    "ENVIRONMENT": "testing",
    "TESTING": True,
    "CELERY_TASK_ALWAYS_EAGER": True,  # Run tasks synchronously in testing
    "DATABASE_URL": "postgresql+asyncpg://postgres:0502747598@localhost:5432/compass_test",
    "REDIS_URL": "redis://localhost:6379/1"
} if os.getenv("TESTING") == "True" else {}

settings = Settings(**test_values)
