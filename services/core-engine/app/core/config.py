"""
Core Engine Configuration Settings

Configuration management for the Core Engine service using Pydantic settings.
"""

from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Core Engine service configuration."""
    
    # Application settings
    APP_NAME: str = "Core Engine Service"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False, env="DEBUG")
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    
    # Server settings
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    
    # Database settings
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    DATABASE_POOL_SIZE: int = Field(default=10, env="DATABASE_POOL_SIZE")
    DATABASE_MAX_OVERFLOW: int = Field(default=20, env="DATABASE_MAX_OVERFLOW")
    
    # Redis settings
    REDIS_URL: str = Field(..., env="REDIS_URL")
    REDIS_POOL_SIZE: int = Field(default=10, env="REDIS_POOL_SIZE")
    REDIS_TTL: int = Field(default=3600, env="REDIS_TTL")
      # AI Model settings
    OPENAI_API_KEY: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    MODEL_NAME: str = Field(default="gpt-4", env="MODEL_NAME")
    MAX_TOKENS: int = Field(default=2000, env="MAX_TOKENS")
    TEMPERATURE: float = Field(default=0.7, env="TEMPERATURE")
    
    # Vector Database settings
    WEAVIATE_URL: str = Field(..., env="WEAVIATE_URL")
    WEAVIATE_API_KEY: Optional[str] = Field(default=None, env="WEAVIATE_API_KEY")
    
    # Security settings
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # Logging settings
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    ENABLE_JSON_LOGGING: bool = Field(default=True, env="ENABLE_JSON_LOGGING")
    LOG_FILE: Optional[str] = Field(default=None, env="LOG_FILE")
    
    # Monitoring settings
    ENABLE_METRICS: bool = Field(default=True, env="ENABLE_METRICS")
    METRICS_PORT: int = Field(default=9090, env="METRICS_PORT")
      # Service URLs
    VOICE_MODULE_URL: str = Field(default="http://localhost:8001", env="VOICE_MODULE_URL")
    DOCUMENT_MODULE_URL: str = Field(default="http://localhost:8002", env="DOCUMENT_MODULE_URL")
    API_GATEWAY_URL: str = Field(default="http://localhost:8080", env="API_GATEWAY_URL")
    
    # Processing settings
    MAX_CONVERSATION_HISTORY: int = Field(default=50, env="MAX_CONVERSATION_HISTORY")
    CONTEXT_WINDOW_SIZE: int = Field(default=4000, env="CONTEXT_WINDOW_SIZE")
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    def get_allowed_origins(self) -> List[str]:
        """Get CORS allowed origins."""
        return ["http://localhost:3000", "http://localhost:8080", "*"]


# Create settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get settings instance for dependency injection."""
    return settings