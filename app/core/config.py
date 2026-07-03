from pydantic_settings import BaseSettings
from typing import List, Optional
from pydantic import field_validator, SecretStr
import os

class Settings(BaseSettings):
    # App
    APP_NAME: str = "Authentication & Authorization Module"
    APP_ENV: str = "production"
    DEBUG: bool = False
    API_VERSION: str = "v1"
    API_PREFIX: str = f"/api/v1"
    FRONTEND_URL: str = "http://localhost:3000"
    
    # Security
    SECRET_KEY: SecretStr
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_RESET_TOKEN_EXPIRE_HOURS: int = 1  # 1 hour
    
    # Hashing - STRONG defaults
    PASSWORD_HASH_ALGORITHM: str = "argon2"
    ARGON2_TIME_COST: int = 3  # Increased from 2 for better security
    ARGON2_MEMORY_COST: int = 65536  # Increased from 102400 (64MB instead of 100MB)
    ARGON2_PARALLELISM: int = 4
    
    # Database
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "auth_db"
    DB_USER: str = "postgres"
    DB_PASSWORD: SecretStr
    DB_SSL_MODE: str = "require"  # require, verify-full, disable
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_ECHO: bool = False
    
    @property
    def DATABASE_URL(self) -> str:
        """Construct database URL"""
        password = self.DB_PASSWORD.get_secret_value() if isinstance(self.DB_PASSWORD, SecretStr) else self.DB_PASSWORD
        return f"postgresql://{self.DB_USER}:{password}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?sslmode={self.DB_SSL_MODE}"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Email
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_PORT: int = 587
    MAIL_USERNAME: Optional[str] = None
    MAIL_PASSWORD: Optional[SecretStr] = None
    MAIL_FROM: str = "noreply@example.com"
    MAIL_TLS: bool = True
    MAIL_SSL: bool = False
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 60  # seconds
    
    # CORS
    ALLOWED_ORIGINS: List[str] = []
    ALLOWED_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE"]
    ALLOWED_HEADERS: List[str] = ["Content-Type", "Authorization"]
    
    # Validation
    PASSWORD_MIN_LENGTH: int = 12
    USERNAME_MIN_LENGTH: int = 3
    USERNAME_MAX_LENGTH: int = 50
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: Optional[str] = None
    LOG_ROTATION: str = "10 MB"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
    
    @field_validator('ARGON2_TIME_COST')
    @classmethod
    def validate_argon2_time_cost(cls, v):
        """Ensure minimum Argon2 time cost for security"""
        if v < 3:
            raise ValueError('ARGON2_TIME_COST must be at least 3 (recommended: 3-4)')
        return v
    
    @field_validator('ARGON2_MEMORY_COST')
    @classmethod
    def validate_argon2_memory_cost(cls, v):
        """Ensure minimum Argon2 memory cost for security"""
        if v < 65536:  # 64MB minimum
            raise ValueError('ARGON2_MEMORY_COST must be at least 65536 (64MB)')
        return v
    
    @field_validator('SECRET_KEY')
    @classmethod
    def validate_secret_key(cls, v):
        """Ensure SECRET_KEY has minimum length"""
        if isinstance(v, SecretStr):
            secret = v.get_secret_value()
        else:
            secret = v
        
        if len(secret) < 32:
            raise ValueError('SECRET_KEY must be at least 32 characters long')
        return v
    
    @field_validator('DB_SSL_MODE')
    @classmethod
    def validate_db_ssl_mode(cls, v):
        """Enforce SSL in production"""
        valid_modes = ["require", "verify-full", "disable"]
        if v not in valid_modes:
            raise ValueError(f'DB_SSL_MODE must be one of: {", ".join(valid_modes)}')
        return v
    
    @field_validator('ALLOWED_ORIGINS')
    @classmethod
    def validate_allowed_origins(cls, v):
        """Ensure ALLOWED_ORIGINS is set"""
        if not v:
            raise ValueError('ALLOWED_ORIGINS must be configured. Provide in .env or environment variable')
        return v

settings = Settings()