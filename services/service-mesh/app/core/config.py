"""
Configuration settings for Service Mesh
"""
import os
from pydantic import BaseSettings
from loguru import logger


class Settings(BaseSettings):
    """
    Application settings.
    
    Attributes:
        APP_NAME: Name of the application
        APP_VERSION: Version of the application
        DEBUG: Debug mode flag
        PORT: Port to run the application on
        LOG_LEVEL: Logging level
        REDIS_HOST: Redis host
        REDIS_PORT: Redis port
        SERVICE_DISCOVERY_HOST: Service Discovery host
        SERVICE_DISCOVERY_PORT: Service Discovery port
        CONFIG_FILE: Path to the mesh configuration file
        TRACING_ENABLED: Whether distributed tracing is enabled
        METRICS_ENABLED: Whether metrics collection is enabled
        CIRCUIT_BREAKER_ENABLED: Whether circuit breaking is enabled
        RATE_LIMIT_ENABLED: Whether rate limiting is enabled
        MTLS_ENABLED: Whether mTLS is enabled
    """
    APP_NAME: str = "Service Mesh"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    PORT: int = int(os.getenv("PORT", 8600))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Redis
    REDIS_HOST: str = os.getenv("REDIS_HOST", "redis")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))
    
    # Service Discovery
    SERVICE_DISCOVERY_HOST: str = os.getenv("SERVICE_DISCOVERY_HOST", "service-discovery")
    SERVICE_DISCOVERY_PORT: int = int(os.getenv("SERVICE_DISCOVERY_PORT", 8000))
    
    # Configuration
    CONFIG_FILE: str = os.getenv("CONFIG_FILE", "mesh_config.yaml")
    
    # Features
    TRACING_ENABLED: bool = os.getenv("TRACING_ENABLED", "True").lower() == "true"
    METRICS_ENABLED: bool = os.getenv("METRICS_ENABLED", "True").lower() == "true"
    CIRCUIT_BREAKER_ENABLED: bool = os.getenv("CIRCUIT_BREAKER_ENABLED", "True").lower() == "true"
    RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "True").lower() == "true"
    MTLS_ENABLED: bool = os.getenv("MTLS_ENABLED", "False").lower() == "true"
    
    # Circuit Breaker Settings
    CIRCUIT_BREAKER_THRESHOLD: int = int(os.getenv("CIRCUIT_BREAKER_THRESHOLD", 5))
    CIRCUIT_BREAKER_TIMEOUT: int = int(os.getenv("CIRCUIT_BREAKER_TIMEOUT", 30))
    
    # Rate Limit Settings
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", 100))
    RATE_LIMIT_WINDOW: int = int(os.getenv("RATE_LIMIT_WINDOW", 60))
    
    # CORS Settings
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "*")
    CORS_METHODS: str = os.getenv("CORS_METHODS", "GET,POST,PUT,DELETE,OPTIONS")
    CORS_HEADERS: str = os.getenv("CORS_HEADERS", "*")
    
    class Config:
        """Pydantic config class"""
        env_file = ".env"


# Create settings instance
settings = Settings()

# Configure logger
logger.remove()
logger.add(
    "service_mesh.log",
    level=settings.LOG_LEVEL,
    rotation="10 MB",
    retention="1 week",
)
logger.add(lambda msg: print(msg, end=""), level=settings.LOG_LEVEL)

logger.info(f"Loaded configuration for {settings.APP_NAME} v{settings.APP_VERSION}")