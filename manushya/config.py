"""
Configuration management for Manushya.ai
"""

import os
from typing import Optional, List, Union
from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application
    app_name: str = "Manushya.ai"
    version: str = "0.1.0"
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Server
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    workers: int = Field(default=1, env="WORKERS")
    
    # Security
    secret_key: str = Field(..., env="SECRET_KEY")
    jwt_secret_key: str = Field(..., env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_expiration_minutes: int = Field(default=30, env="JWT_EXPIRATION_MINUTES")
    encryption_key: str = Field(..., env="ENCRYPTION_KEY")
    
    # Database
    database_url: str = Field(..., env="DATABASE_URL")
    database_pool_size: int = Field(default=10, env="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=20, env="DATABASE_MAX_OVERFLOW")
    
    # Redis
    redis_url: str = Field(..., env="REDIS_URL")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    redis_db: int = Field(default=0, env="REDIS_DB")
    
    # Celery
    celery_broker_url: str = Field(..., env="CELERY_BROKER_URL")
    celery_result_backend: str = Field(..., env="CELERY_RESULT_BACKEND")
    celery_task_serializer: str = Field(default="json", env="CELERY_TASK_SERIALIZER")
    celery_result_serializer: str = Field(default="json", env="CELERY_RESULT_SERIALIZER")
    celery_accept_content: str = Field(default="json", env="CELERY_ACCEPT_CONTENT")
    
    # CORS
    cors_origins: str = Field(default="*", env="CORS_ORIGINS")
    cors_allow_credentials: bool = Field(default=True, env="CORS_ALLOW_CREDENTIALS")
    cors_allow_methods: str = Field(default="*", env="CORS_ALLOW_METHODS")
    cors_allow_headers: str = Field(default="*", env="CORS_ALLOW_HEADERS")
    
    # Rate Limiting
    rate_limit_per_minute: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    rate_limit_per_hour: int = Field(default=1000, env="RATE_LIMIT_PER_HOUR")
    
    # Memory & Vector Settings
    vector_dimension: int = Field(default=1536, env="VECTOR_DIMENSION")  # OpenAI ada-002 default
    max_memory_size: int = Field(default=10000, env="MAX_MEMORY_SIZE")  # characters
    memory_ttl_days: int = Field(default=365, env="MEMORY_TTL_DAYS")
    
    # Embedding Service
    embedding_service_url: Optional[str] = Field(default=None, env="EMBEDDING_SERVICE_URL")
    embedding_service_api_key: Optional[str] = Field(default=None, env="EMBEDDING_SERVICE_API_KEY")
    embedding_model: str = Field(default="text-embedding-ada-002", env="EMBEDDING_MODEL")
    
    # Webhooks
    webhook_timeout: int = Field(default=10, env="WEBHOOK_TIMEOUT")
    webhook_retry_attempts: int = Field(default=3, env="WEBHOOK_RETRY_ATTEMPTS")
    
    # Audit & Compliance
    audit_log_retention_days: int = Field(default=2555, env="AUDIT_LOG_RETENTION_DAYS")  # 7 years
    gdpr_enabled: bool = Field(default=True, env="GDPR_ENABLED")
    
    # Monitoring
    metrics_enabled: bool = Field(default=True, env="METRICS_ENABLED")
    health_check_timeout: int = Field(default=5, env="HEALTH_CHECK_TIMEOUT")
    
    # Extra fields for compatibility with .env
    postgres_password: Optional[str] = Field(default=None, env="POSTGRES_PASSWORD")
    flower_user: Optional[str] = Field(default=None, env="FLOWER_USER")
    flower_password: Optional[str] = Field(default=None, env="FLOWER_PASSWORD")
    
    @validator("encryption_key")
    def validate_encryption_key(cls, v):
        """Validate encryption key is 32 bytes (256 bits)."""
        if len(v.encode()) != 32:
            raise ValueError("Encryption key must be exactly 32 bytes")
        return v
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins as a list."""
        if self.cors_origins == "*":
            return ["*"]
        return [item.strip() for item in self.cors_origins.split(",")]
    
    @property
    def cors_allow_methods_list(self) -> List[str]:
        """Get CORS allow methods as a list."""
        if self.cors_allow_methods == "*":
            return ["*"]
        return [item.strip() for item in self.cors_allow_methods.split(",")]
    
    @property
    def cors_allow_headers_list(self) -> List[str]:
        """Get CORS allow headers as a list."""
        if self.cors_allow_headers == "*":
            return ["*"]
        return [item.strip() for item in self.cors_allow_headers.split(",")]
    
    @property
    def celery_accept_content_list(self) -> List[str]:
        """Get Celery accept content as a list."""
        return [item.strip() for item in self.celery_accept_content.split(",")]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get settings instance for dependency injection."""
    return settings 