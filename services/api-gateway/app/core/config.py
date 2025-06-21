"""
Configuration settings for the API Gateway Service
"""
import os
from typing import List, Dict, Any, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application settings"""
    
    # Application info
    APP_NAME: str = os.environ.get("APP_NAME", "API Gateway")
    APP_DESCRIPTION: str = os.environ.get("APP_DESCRIPTION", "API Gateway for the AI Voice Agent platform")
    APP_VERSION: str = os.environ.get("APP_VERSION", "1.0.0")

    # Environment
    ENVIRONMENT: str = os.environ.get("ENVIRONMENT", "development")
    DEBUG: bool = os.environ.get("DEBUG", "True").lower() in ("true", "1", "t", "yes")
    LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")
    
    # Server settings
    HOST: str = os.environ.get("HOST", "0.0.0.0")
    PORT: int = int(os.environ.get("PORT", "8000"))
    WORKERS: int = int(os.environ.get("WORKERS", "1"))

    # API settings
    API_V1_STR: str = "/api/v1"

    # CORS
    CORS_ORIGINS: List[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]

    # Metrics
    ENABLE_METRICS: bool = True

    # Security settings
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "changeme_this_is_not_secure_for_production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

    # Redis settings for rate limiting
    REDIS_HOST: str = os.environ.get("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.environ.get("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.environ.get("REDIS_DB", "0"))
    REDIS_PASSWORD: Optional[str] = os.environ.get("REDIS_PASSWORD")

    # Service discovery settings
    SERVICE_DISCOVERY_URL: str = os.environ.get("SERVICE_DISCOVERY_URL", "http://service-discovery:8000")

    # Circuit breaker settings
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = int(os.environ.get("CIRCUIT_BREAKER_FAILURE_THRESHOLD", "5"))
    CIRCUIT_BREAKER_RECOVERY_TIMEOUT: int = int(os.environ.get("CIRCUIT_BREAKER_RECOVERY_TIMEOUT", "30"))
    CIRCUIT_BREAKER_HALF_OPEN_MAX_CALLS: int = int(os.environ.get("CIRCUIT_BREAKER_HALF_OPEN_MAX_CALLS", "3"))

    # Cache settings
    CACHE_TTL: int = int(os.environ.get("CACHE_TTL", "60"))  # seconds

    # Service routing configuration
    # Default service routes that can be overridden by environment variables
    SERVICE_ROUTES: Dict[str, Dict[str, Any]] = {
        "realtime-voice": {
            "prefix": os.environ.get("VOICE_SERVICE_PREFIX", "/voice"),
            "target": os.environ.get("VOICE_SERVICE_TARGET", "http://realtime-voice:8000"),
            "timeout": int(os.environ.get("VOICE_SERVICE_TIMEOUT", "30")),
            "retry_count": int(os.environ.get("VOICE_SERVICE_RETRY_COUNT", "3"))
        },
        "edge-ai": {
            "prefix": os.environ.get("EDGE_AI_SERVICE_PREFIX", "/edge-ai"),
            "target": os.environ.get("EDGE_AI_SERVICE_TARGET", "http://edge-ai:8500"),
            "timeout": int(os.environ.get("EDGE_AI_SERVICE_TIMEOUT", "10")),
            "retry_count": int(os.environ.get("EDGE_AI_SERVICE_RETRY_COUNT", "2"))
        },
        "graphql-api": {
            "prefix": os.environ.get("GRAPHQL_SERVICE_PREFIX", "/graphql"),
            "target": os.environ.get("GRAPHQL_SERVICE_TARGET", "http://graphql-api:4000"),
            "timeout": int(os.environ.get("GRAPHQL_SERVICE_TIMEOUT", "15")),
            "retry_count": int(os.environ.get("GRAPHQL_SERVICE_RETRY_COUNT", "2"))
        }
    }

    # Model config
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

# Create settings instance
settings = Settings()