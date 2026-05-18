"""
Configuration management for CBT system using Pydantic settings.
"""

from typing import List, Optional
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        extra="ignore",
        env_file=".env",
        case_sensitive=False,
    )

    # Application Configuration
    app_name: str = Field(default="CBT System")
    app_version: str = Field(default="1.0.0")
    debug: bool = Field(default=False)
    environment: str = Field(default="development")
    api_v1_str: str = Field(default="/api/v1")
    port: int = Field(default=8000, description="HTTP port for uvicorn (local overrides via PORT).")

    # Database Configuration
    database_url: Optional[str] = None
    database_host: str = Field(default="localhost")
    database_port: int = Field(default=27017)
    database_name: str = Field(default="cbt_db")
    database_user: str = Field(default="cbt_user")
    database_password: str = Field(default="")

    # Redis Configuration
    redis_url: Optional[str] = None
    redis_host: str = Field(default="localhost")
    redis_port: int = Field(default=6379)
    redis_db: int = Field(default=0)
    redis_password: Optional[str] = None

    # JWT Configuration
    jwt_secret: str = Field(...)
    jwt_algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=15)
    refresh_token_expire_days: int = Field(default=7)
    jwt_issuer: str = Field(default="cbt-system")
    jwt_audience: str = Field(default="cbt-users")

    # Security Configuration
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"]
    )
    allowed_hosts: List[str] = Field(
        default=["localhost", "127.0.0.1"]
    )
    secret_key: str = Field(...)
    randomisation_secret: str = Field(
        ...,
        description="Server-side secret used to derive deterministic exam randomisation seeds."
    )

    # Biometric Configuration
    biometric_encryption_key: str = Field(...)
    fingerprint_threshold: float = Field(default=85.0)
    facial_threshold: float = Field(default=80.0)
    voice_threshold: float = Field(default=75.0)

    @field_validator("biometric_encryption_key")
    @classmethod
    def validate_biometric_key(cls, v: str) -> str:
        """Validate biometric encryption key length."""
        if len(v.encode()) < 32:
            raise ValueError("Biometric encryption key must be at least 32 bytes")
        return v

    # Email Configuration
    smtp_host: Optional[str] = None
    smtp_port: int = Field(default=587)
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    email_from: Optional[str] = None
    email_from_name: str = Field(default="CBT System")

    # File Upload Configuration
    upload_dir: str = Field(default="./uploads")
    max_file_size: int = Field(default=10485760)  # 10MB
    allowed_extensions: List[str] = Field(
        default=["pdf", "doc", "docx", "csv", "txt"]
    )

    # Logging Configuration
    log_level: str = Field(default="INFO")
    log_file: str = Field(default="./logs/cbt.log")
    log_max_size: int = Field(default=10485760)  # 10MB
    log_backup_count: int = Field(default=5)

    # Session Configuration
    session_cookie_name: str = Field(default="cbt_session")
    session_cookie_secure: bool = Field(default=False)
    session_cookie_httponly: bool = Field(default=True)
    session_cookie_samesite: str = Field(default="lax")
    max_concurrent_sessions: int = Field(default=3)
    session_timeout_minutes: int = Field(default=120)
    idle_timeout_minutes: int = Field(default=30)

    # Rate Limiting
    rate_limit_per_minute: int = Field(default=100)
    rate_limit_burst: int = Field(default=200)

    # Monitoring and Health
    health_check_interval: int = Field(default=30)
    metrics_enabled: bool = Field(default=True)

    @model_validator(mode="after")
    def assemble_connection_urls(self):
        """Backfill connection URLs from component parts when omitted."""
        if not self.database_url:
            host = self.database_host
            port = self.database_port
            auth = ""
            if self.database_user:
                pw = f":{self.database_password}" if self.database_password else ""
                auth = f"{self.database_user}{pw}@"
            self.database_url = f"mongodb://{auth}{host}:{port}"

        if not str(self.database_url).lower().startswith("mongodb"):
            raise ValueError(
                "DATABASE_URL must be a MongoDB connection string (e.g. mongodb://localhost:27017)."
            )

        if not self.redis_url:
            password_part = f":{self.redis_password}@" if self.redis_password else ""
            self.redis_url = (
                f"redis://{password_part}"
                f"{self.redis_host}:"
                f"{self.redis_port}/"
                f"{self.redis_db}"
            )
        return self

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment.lower() in {"development", "dev", "local"}

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
