"""Application configuration using Pydantic settings."""

from typing import List
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseModel):
    """Database configuration settings."""

    url: str = Field(
        default="sqlite+aiosqlite:///./sre_agent.db",
        description="Database URL (PostgreSQL, SQLite, etc.)",
    )
    pool_size: int = Field(default=10, description="Database connection pool size")
    max_overflow: int = Field(default=20, description="Maximum overflow connections")
    echo: bool = Field(default=False, description="Echo SQL queries")


class RedisSettings(BaseModel):
    """Redis configuration settings."""

    url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL",
    )
    max_connections: int = Field(default=50, description="Maximum Redis connections")
    decode_responses: bool = Field(default=True, description="Decode Redis responses")


class Neo4jSettings(BaseModel):
    """Neo4j graph database configuration settings."""

    uri: str = Field(default="bolt://localhost:7687", description="Neo4j connection URI")
    user: str = Field(default="neo4j", description="Neo4j username")
    password: str = Field(default="neo4j_password", description="Neo4j password")
    max_connection_lifetime: int = Field(
        default=3600, description="Maximum connection lifetime in seconds"
    )


class LLMSettings(BaseModel):
    """LLM provider configuration settings."""

    provider: str = Field(
        default="openai",
        description="LLM provider: 'openai', 'azure', or 'anthropic'",
    )
    
    # OpenAI settings
    openai_api_key: str | None = Field(
        default=None,
        description="OpenAI API key",
    )
    openai_model: str = Field(
        default="gpt-4o",
        description="OpenAI model name",
    )
    
    # Azure OpenAI settings
    azure_openai_endpoint: str | None = Field(
        default=None,
        description="Azure OpenAI endpoint URL",
    )
    azure_openai_api_key: str | None = Field(
        default=None,
        description="Azure OpenAI API key",
    )
    azure_openai_deployment_name: str | None = Field(
        default=None,
        description="Azure OpenAI deployment name",
    )
    azure_openai_api_version: str = Field(
        default="2024-08-01-preview",
        description="Azure OpenAI API version",
    )
    
    # Anthropic settings
    anthropic_api_key: str | None = Field(
        default=None,
        description="Anthropic API key",
    )
    anthropic_model: str = Field(
        default="claude-3-5-sonnet-20241022",
        description="Anthropic model name",
    )
    
    # Common settings
    temperature: float = Field(
        default=0.0,
        description="LLM temperature (0.0 = deterministic)",
    )
    max_tokens: int = Field(
        default=4096,
        description="Maximum tokens in response",
    )


class AppSettings(BaseModel):
    """Main application settings."""

    app_name: str = Field(default="SRE AI Agent", description="Application name")
    app_env: str = Field(default="development", description="Application environment")
    log_level: str = Field(default="INFO", description="Logging level")
    secret_key: str = Field(default="dev-secret-key-change-in-production", description="Secret key for JWT and encryption")
    allowed_origins: List[str] = Field(
        default_factory=lambda: ["http://localhost:3000"],
        description="CORS allowed origins",
    )
    api_v1_prefix: str = Field(default="/api/v1", description="API v1 route prefix")

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_origins(cls, v: str | List[str]) -> List[str]:
        """Parse comma-separated origins string into list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v


class Settings(BaseSettings):
    """Aggregated application settings."""

    # App settings
    app_name: str = Field(default="SRE AI Agent", validation_alias="APP_NAME")
    app_env: str = Field(default="development", validation_alias="APP_ENV")
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    secret_key: str = Field(default="dev-secret-key-change-in-production", validation_alias="SECRET_KEY")
    allowed_origins: str = Field(default="http://localhost:3000", validation_alias="ALLOWED_ORIGINS")
    api_v1_prefix: str = Field(default="/api/v1", validation_alias="API_V1_PREFIX")
    
    # Database settings
    database_url: str = Field(default="sqlite+aiosqlite:///./sre_agent.db", validation_alias="DATABASE_URL")
    database_pool_size: int = Field(default=10, validation_alias="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=20, validation_alias="DATABASE_MAX_OVERFLOW")
    database_echo: bool = Field(default=False, validation_alias="DATABASE_ECHO")
    
    # Redis settings
    redis_url: str = Field(default="redis://localhost:6379/0", validation_alias="REDIS_URL")
    redis_max_connections: int = Field(default=50, validation_alias="REDIS_MAX_CONNECTIONS")
    redis_decode_responses: bool = Field(default=True, validation_alias="REDIS_DECODE_RESPONSES")
    
    # Neo4j settings
    neo4j_uri: str = Field(default="bolt://localhost:7687", validation_alias="NEO4J_URI")
    neo4j_user: str = Field(default="neo4j", validation_alias="NEO4J_USER")
    neo4j_password: str = Field(default="neo4j_password", validation_alias="NEO4J_PASSWORD")
    neo4j_max_connection_lifetime: int = Field(default=3600, validation_alias="NEO4J_MAX_CONNECTION_LIFETIME")
    
    # LLM settings
    llm_provider: str = Field(default="openai", validation_alias="LLM_PROVIDER")
    openai_api_key: str | None = Field(default=None, validation_alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o", validation_alias="OPENAI_MODEL")
    azure_openai_endpoint: str | None = Field(default=None, validation_alias="AZURE_OPENAI_ENDPOINT")
    azure_openai_api_key: str | None = Field(default=None, validation_alias="AZURE_OPENAI_API_KEY")
    azure_openai_deployment_name: str | None = Field(default=None, validation_alias="AZURE_OPENAI_DEPLOYMENT_NAME")
    azure_openai_api_version: str = Field(default="2024-08-01-preview", validation_alias="AZURE_OPENAI_API_VERSION")
    anthropic_api_key: str | None = Field(default=None, validation_alias="ANTHROPIC_API_KEY")
    anthropic_model: str = Field(default="claude-3-5-sonnet-20241022", validation_alias="ANTHROPIC_MODEL")
    llm_temperature: float = Field(default=0.0, validation_alias="LLM_TEMPERATURE")
    llm_max_tokens: int = Field(default=4096, validation_alias="LLM_MAX_TOKENS")
    
    # ServiceNow settings
    servicenow_instance_url: str | None = Field(default=None, validation_alias="SERVICENOW_INSTANCE_URL")
    servicenow_username: str | None = Field(default=None, validation_alias="SERVICENOW_USERNAME")
    servicenow_password: str | None = Field(default=None, validation_alias="SERVICENOW_PASSWORD")
    
    # AWS settings
    aws_default_region: str = Field(default="us-east-1", validation_alias="AWS_DEFAULT_REGION")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    @property
    def app(self) -> AppSettings:
        """Get app settings."""
        origins = [o.strip() for o in self.allowed_origins.split(",")]
        return AppSettings(
            app_name=self.app_name,
            app_env=self.app_env,
            log_level=self.log_level,
            secret_key=self.secret_key,
            allowed_origins=origins,
            api_v1_prefix=self.api_v1_prefix,
        )
    
    @property
    def database(self) -> DatabaseSettings:
        """Get database settings."""
        return DatabaseSettings(
            url=self.database_url,
            pool_size=self.database_pool_size,
            max_overflow=self.database_max_overflow,
            echo=self.database_echo,
        )
    
    @property
    def redis(self) -> RedisSettings:
        """Get redis settings."""
        return RedisSettings(
            url=self.redis_url,
            max_connections=self.redis_max_connections,
            decode_responses=self.redis_decode_responses,
        )
    
    @property
    def neo4j(self) -> Neo4jSettings:
        """Get neo4j settings."""
        return Neo4jSettings(
            uri=self.neo4j_uri,
            user=self.neo4j_user,
            password=self.neo4j_password,
            max_connection_lifetime=self.neo4j_max_connection_lifetime,
        )
    
    @property
    def llm(self) -> LLMSettings:
        """Get LLM settings."""
        return LLMSettings(
            provider=self.llm_provider,
            openai_api_key=self.openai_api_key,
            openai_model=self.openai_model,
            azure_openai_endpoint=self.azure_openai_endpoint,
            azure_openai_api_key=self.azure_openai_api_key,
            azure_openai_deployment_name=self.azure_openai_deployment_name,
            azure_openai_api_version=self.azure_openai_api_version,
            anthropic_api_key=self.anthropic_api_key,
            anthropic_model=self.anthropic_model,
            temperature=self.llm_temperature,
            max_tokens=self.llm_max_tokens,
        )


def get_settings() -> Settings:
    """Get application settings instance.

    Returns:
        Settings: Application settings
    """
    return Settings()
