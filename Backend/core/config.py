from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "COMPASS"
    VERSION: str = "1.0"


    
    # Database Configs
    DATABASE_URL: str = "postgresql+asyncpg://ahmed:0502747598@localhost:5432/compass"

    # Redis Configs
    REDIS_URL: str = "redis://localhost:6379/0"

    class Config:
        env_file = ".env"  # Load variables from .env


settings = Settings()
