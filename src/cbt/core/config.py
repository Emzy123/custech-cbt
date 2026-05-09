"""
Configuration management for CBT system using Pydantic settings.
"""

import os
from typing import List, Optional
from pydantic import validator, Field
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    model_config = {
        "extra": "ignore",
        "env_file": ".env",
        "case_sensitive": False
    }
    
    # Application Configuration
    app_name: str = Field(default="CBT System", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    environment: str = Field(default="development", env="ENVIRONMENT")
    api_v1_str: str = Field(default="/api/v1", env="API_V1_STR")
    
    # Database Configuration
    database_url: Optional[str] = Field(None, env="DATABASE_URL")
    database_host: str = Field(default="localhost", env="DATABASE_HOST")
    database_port: int = Field(default=5432, env="DATABASE_PORT")
    database_name: str = Field(default="cbt_db", env="DATABASE_NAME")
    database_user: str = Field(default="cbt_user", env="DATABASE_USER")
    database_password: str = Field(default="", env="DATABASE_PASSWORD")
    
    @validator("database_url", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: dict) -> str:
        """Return MongoDB URL from env or default to localhost."""
        if isinstance(v, str) and v:
            return v
        return "mongodb://localhost:27017"
    
    # Redis Configuration
    redis_url: Optional[str] = Field(None, env="REDIS_URL")
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_db: int = Field(default=0, env="REDIS_DB")
    redis_password: Optional[str] = Field(None, env="REDIS_PASSWORD")
    
    @validator("redis_url", pre=True)
    def assemble_redis_connection(cls, v: Optional[str], values: dict) -> str:
        """Assemble Redis URL from components if not provided."""
        if isinstance(v, str):
            return v
        
        password_part = f":{values.get('redis_password')}@" if values.get('redis_password') else ""
        return (
            f"redis://{password_part}"
            f"{values.get('redis_host')}:"
            f"{values.get('redis_port')}/"
            f"{values.get('redis_db')}"
        )
    
    # JWT Configuration
    jwt_secret: str = Field(..., env="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=15, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=7, env="REFRESH_TOKEN_EXPIRE_DAYS")
    jwt_issuer: str = Field(default="cbt-system", env="JWT_ISSUER")
    jwt_audience: str = Field(default="cbt-users", env="JWT_AUDIENCE")
    
    # Security Configuration
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        env="CORS_ORIGINS"
    )
    allowed_hosts: List[str] = Field(
        default=["localhost", "127.0.0.1"],
        env="ALLOWED_HOSTS"
    )
    secret_key: str = Field(..., env="SECRET_KEY")
    
    # Biometric Configuration
    biometric_encryption_key: str = Field(..., env="BIOMETRIC_ENCRYPTION_KEY")
    fingerprint_threshold: float = Field(default=85.0, env="FINGERPRINT_THRESHOLD")
    facial_threshold: float = Field(default=80.0, env="FACIAL_THRESHOLD")
    voice_threshold: float = Field(default=75.0, env="VOICE_THRESHOLD")
    
    @validator("biometric_encryption_key")
    def validate_biometric_key(cls, v: str) -> str:
        """Validate biometric encryption key length."""
        if len(v.encode()) < 32:
            raise ValueError("Biometric encryption key must be at least 32 bytes")
        return v
    
    # Email Configuration
    smtp_host: Optional[str] = Field(None, env="SMTP_HOST")
    smtp_port: int = Field(default=587, env="SMTP_PORT")
    smtp_user: Optional[str] = Field(None, env="SMTP_USER")
    smtp_password: Optional[str] = Field(None, env="SMTP_PASSWORD")
    email_from: Optional[str] = Field(None, env="EMAIL_FROM")
    email_from_name: str = Field(default="CBT System", env="EMAIL_FROM_NAME")
    
    # File Upload Configuration
    upload_dir: str = Field(default="./uploads", env="UPLOAD_DIR")
    max_file_size: int = Field(default=10485760, env="MAX_FILE_SIZE")  # 10MB
    allowed_extensions: List[str] = Field(
        default=["pdf", "doc", "docx", "csv", "txt"],
        env="ALLOWED_EXTENSIONS"
    )
    
    # Logging Configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: str = Field(default="./logs/cbt.log", env="LOG_FILE")
    log_max_size: int = Field(default=10485760, env="LOG_MAX_SIZE")  # 10MB
    log_backup_count: int = Field(default=5, env="LOG_BACKUP_COUNT")
    
    # Session Configuration
    session_cookie_name: str = Field(default="cbt_session", env="SESSION_COOKIE_NAME")
    session_cookie_secure: bool = Field(default=False, env="SESSION_COOKIE_SECURE")
    session_cookie_httponly: bool = Field(default=True, env="SESSION_COOKIE_HTTPONLY")
    session_cookie_samesite: str = Field(default="lax", env="SESSION_COOKIE_SAMESITE")
    max_concurrent_sessions: int = Field(default=3, env="MAX_CONCURRENT_SESSIONS")
    session_timeout_minutes: int = Field(default=120, env="SESSION_TIMEOUT_MINUTES")
    idle_timeout_minutes: int = Field(default=30, env="IDLE_TIMEOUT_MINUTES")
    
    # Rate Limiting
    rate_limit_per_minute: int = Field(default=100, env="RATE_LIMIT_PER_MINUTE")
    rate_limit_burst: int = Field(default=200, env="RATE_LIMIT_BURST")
    
    # Monitoring and Health
    health_check_interval: int = Field(default=30, env="HEALTH_CHECK_INTERVAL")
    metrics_enabled: bool = Field(default=True, env="METRICS_ENABLED")
    
            
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment.lower() == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment.lower() == "production"
    
    @property
    def is_testing(self) -> bool:
        """Check if running in testing mode."""
        return self.environment.lower() == "testing"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
