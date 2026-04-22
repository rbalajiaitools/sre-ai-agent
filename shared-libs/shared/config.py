"""Shared configuration settings."""

from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database configuration."""
    
    model_config = SettingsConfigDict(env_prefix="CSAA_DATABASE_")
    
    url: str = Field(
        default="postgresql+asyncpg://astra_user:astra_password@localhost:5432/astra_db",
        description="PostgreSQL connection URL"
    )
    pool_size: int = Field(default=20, description="Connection pool size")
    max_overflow: int = Field(default=10, description="Max overflow connections")
    echo: bool = Field(default=False, description="Echo SQL queries")


class RedisSettings(BaseSettings):
    """Redis configuration."""
    
    model_config = SettingsConfigDict(env_prefix="CSAA_REDIS_")
    
    url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )
    max_connections: int = Field(default=50, description="Max connections in pool")
    decode_responses: bool = Field(default=True, description="Decode responses to strings")


class KafkaSettings(BaseSettings):
    """Kafka configuration."""
    
    model_config = SettingsConfigDict(env_prefix="CSAA_KAFKA_")
    
    bootstrap_servers: str = Field(
        default="localhost:9092",
        description="Kafka bootstrap servers"
    )
    client_id: str = Field(default="astra-ai", description="Kafka client ID")
    group_id: str = Field(default="astra-ai-group", description="Consumer group ID")
    auto_offset_reset: str = Field(default="earliest", description="Auto offset reset")
    enable_auto_commit: bool = Field(default=True, description="Enable auto commit")


class TemporalSettings(BaseSettings):
    """Temporal configuration."""
    
    model_config = SettingsConfigDict(env_prefix="CSAA_TEMPORAL_")
    
    host: str = Field(default="localhost", description="Temporal server host")
    port: int = Field(default=7233, description="Temporal server port")
    namespace: str = Field(default="default", description="Temporal namespace")
    task_queue: str = Field(default="astra-ai-tasks", description="Task queue name")


class JWTSettings(BaseSettings):
    """JWT configuration."""
    
    model_config = SettingsConfigDict(env_prefix="CSAA_JWT_")
    
    secret: str = Field(
        default="your-secret-key-change-in-production",
        description="JWT secret key"
    )
    algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(
        default=30,
        description="Access token expiration in minutes"
    )
    refresh_token_expire_days: int = Field(
        default=7,
        description="Refresh token expiration in days"
    )


class LoggingSettings(BaseSettings):
    """Logging configuration."""
    
    model_config = SettingsConfigDict(env_prefix="CSAA_LOG_")
    
    level: str = Field(default="INFO", description="Log level")
    format: str = Field(default="json", description="Log format (json or console)")


class SharedSettings(BaseSettings):
    """Shared settings for all services."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # Service identification
    service_name: str = Field(default="astra-ai", description="Service name")
    environment: str = Field(default="development", description="Environment")
    
    # Component settings
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    kafka: KafkaSettings = Field(default_factory=KafkaSettings)
    temporal: TemporalSettings = Field(default_factory=TemporalSettings)
    jwt: JWTSettings = Field(default_factory=JWTSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    
    # CORS
    allowed_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        description="Allowed CORS origins"
    )


def get_settings() -> SharedSettings:
    """Get shared settings instance."""
    return SharedSettings()
