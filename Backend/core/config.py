from pydantic_settings import BaseSettings
from typing import List, Optional
from pydantic import validator, AnyHttpUrl, EmailStr
import json
import os


class Settings(BaseSettings):
    # Database settings
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DATABASE_URL: str

    # JWT settings
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # App settings
    APP_NAME: str = "COMPASS"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # Test settings
    TESTING: bool = False
    TEST_DATABASE_URL: Optional[str] = None

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
    REDIS_URL: str = "redis://localhost:6379/0"

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
        return f"redis://{values.get('REDIS_HOST', 'localhost')}:{values.get('REDIS_PORT', 6379)}/{values.get('REDIS_DB', 0)}"

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"
        env_file_encoding = 'utf-8'


# Initialize settings with fallback values for testing
test_values = {
    "DB_USER": "test",
    "DB_PASSWORD": "test",
    "DB_HOST": "localhost",
    "DB_PORT": 5432,
    "DB_NAME": "test_db",
    "JWT_SECRET_KEY": "test_secret_key",
    "APP_NAME": "COMPASS_TEST",
    "APP_VERSION": "test",
    "ENVIRONMENT": "testing",
    "TESTING": True,
} if os.getenv("TESTING") == "True" else {}

settings = Settings(**test_values)
