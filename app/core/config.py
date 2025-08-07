from typing import ClassVar, Optional
from pydantic import AnyHttpUrl, Field, field_validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Coffee Shop API"
    API_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api/v1"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    
    # Security and Authentication
    SECRET_KEY: str
    JWT_SECRET_KEY: str
    JWT_REFRESH_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ISSUER: str = "Coffee Shop API"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    CORS_ORIGINS: list[AnyHttpUrl] = ["http://localhost:3000"]
    
    # Database
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str = "db"
    POSTGRES_PORT: str = "5432"
    DATABASE_URL: Optional[str] = None
    
    @field_validator("DATABASE_URL", mode='before')
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], info) -> str:
        if isinstance(v, str):
            return v
        values = info.data
        return f"postgresql+asyncpg://{values['POSTGRES_USER']}:{values['POSTGRES_PASSWORD']}@{values['POSTGRES_HOST']}:{values['POSTGRES_PORT']}/{values['POSTGRES_DB']}"
    
    # Redis & Celery
    REDIS_PASSWORD: str = ""
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    CELERY_BROKER_URL: Optional[str] = None
    CELERY_BACKEND_URL: Optional[str] = None
    
    @field_validator("CELERY_BROKER_URL", "CELERY_BACKEND_URL", mode='before')
    @classmethod
    def assemble_celery_url(cls, v: Optional[str], info) -> Optional[str]:
        if v:
            return v
        values = info.data
        redis_auth = f":{values['REDIS_PASSWORD']}@" if values["REDIS_PASSWORD"] else ""
        return f"redis://{redis_auth}{values['REDIS_HOST']}:{values['REDIS_PORT']}/{values['REDIS_DB']}"
    
    # Email Configuration
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_TLS: bool = True
    SMTP_FROM_EMAIL: str = "noreply@coffeeshop.com"
    EMAIL_VERIFICATION_ENABLED: bool = True
    FRONTEND_URL: str = "http://localhost:3000"
    
    # Application Settings
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    RATE_LIMIT_PER_MINUTE: int = 100
    
    model_config = {
        "case_sensitive": True,
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }

settings = Settings()
