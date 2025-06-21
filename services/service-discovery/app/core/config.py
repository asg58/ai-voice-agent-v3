"""
Configuration settings for the Service Discovery Service
"""
import os
from typing import List, Dict, Any, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application settings"""
    
    # Application info
    APP_NAME: str = "Service Discovery"
    APP_DESCRIPTION: str = "Service Discovery for the AI Voice Agent platform"
    APP_VERSION: str = "1.0.0"
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 1
    
    # API settings
    API_V1_STR: str = "/api/v1"
    
    # CORS
    CORS_ORIGINS: List[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    
    # Metrics
    ENABLE_METRICS: bool = True
    
    # Service settings
    SERVICE_TTL: int = 60  # seconds
    HEALTH_CHECK_INTERVAL: int = 30  # seconds
    
    # Redis settings for service registry
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    
    # Model config
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

# Create settings instance
settings = Settings()