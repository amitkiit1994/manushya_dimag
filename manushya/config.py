"""
Configuration management for Manushya.ai
"""

from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Application
    app_name: str = "Manushya.ai"
    version: str = "0.1.0"
    environment: str = Field(default="development")
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")

    # Server
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    workers: int = Field(default=1)

    # Security
    secret_key: str = Field(...)
    jwt_secret_key: str = Field(...)
    jwt_algorithm: str = Field(default="HS256")
    jwt_expiration_minutes: int = Field(default=30)
    encryption_key: str = Field(...)

    # Database
    database_url: str = Field(...)
    database_pool_size: int = Field(default=10)
    database_max_overflow: int = Field(default=20)

    # Redis
    redis_url: str = Field(...)
    redis_password: str | None = Field(default=None)
    redis_db: int = Field(default=0)

    # Celery
    celery_broker_url: str = Field(...)
    celery_result_backend: str = Field(...)
    celery_task_serializer: str = Field(default="json")
    celery_result_serializer: str = Field(default="json")
    celery_accept_content: str = Field(default="json")

    # CORS
    cors_origins: str = Field(default="*")
    cors_allow_credentials: bool = Field(default=True)
    cors_allow_methods: str = Field(default="*")
    cors_allow_headers: str = Field(default="*")

    # Rate Limiting
    rate_limit_per_minute: int = Field(default=60)
    rate_limit_per_hour: int = Field(default=1000)

    # Memory & Vector Settings
    vector_dimension: int = Field(default=1536)  # OpenAI ada-002 default
    max_memory_size: int = Field(default=10000)  # characters
    memory_ttl_days: int = Field(default=365)

    # Embedding Service
    embedding_service_url: str | None = Field(default=None)
    embedding_service_api_key: str | None = Field(default=None)
    embedding_model: str = Field(default="text-embedding-ada-002")

    # Webhooks
    webhook_timeout: int = Field(default=10)
    webhook_retry_attempts: int = Field(default=3)

    # Audit & Compliance
    audit_log_retention_days: int = Field(default=2555)  # 7 years
    gdpr_enabled: bool = Field(default=True)

    # Monitoring
    metrics_enabled: bool = Field(default=True)
    health_check_timeout: int = Field(default=5)

    # Extra fields for compatibility with .env
    postgres_password: str | None = Field(default=None)
    flower_user: str | None = Field(default=None)
    flower_password: str | None = Field(default=None)

    @validator("encryption_key")
    def validate_encryption_key(cls, v):
        """Validate encryption key is 32 bytes (256 bits)."""
        if len(v.encode()) != 32:
            raise ValueError("Encryption key must be exactly 32 bytes")
        return v

    @property
    def cors_origins_list(self) -> list[str]:
        """Get CORS origins as a list."""
        if self.cors_origins == "*":
            return ["*"]
        return [item.strip() for item in self.cors_origins.split(",")]

    @property
    def cors_allow_methods_list(self) -> list[str]:
        """Get CORS allow methods as a list."""
        if self.cors_allow_methods == "*":
            return ["*"]
        return [item.strip() for item in self.cors_allow_methods.split(",")]

    @property
    def cors_allow_headers_list(self) -> list[str]:
        """Get CORS allow headers as a list."""
        if self.cors_allow_headers == "*":
            return ["*"]
        return [item.strip() for item in self.cors_allow_headers.split(",")]

    @property
    def celery_accept_content_list(self) -> list[str]:
        """Get Celery accept content as a list."""
        return [item.strip() for item in self.celery_accept_content.split(",")]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()  # type: ignore


def get_settings() -> Settings:
    """Get settings instance for dependency injection."""
    return settings
