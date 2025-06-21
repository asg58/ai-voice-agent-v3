"""
Configuration settings for Dashboard Service
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
        SECRET_KEY: Secret key for JWT token generation
        ALGORITHM: Algorithm for JWT token generation
        ACCESS_TOKEN_EXPIRE_MINUTES: Expiration time for access tokens
        REDIS_HOST: Redis host
        REDIS_PORT: Redis port
        SERVICE_DISCOVERY_HOST: Service Discovery host
        SERVICE_DISCOVERY_PORT: Service Discovery port
    """
    APP_NAME: str = "Dashboard Service"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    PORT: int = int(os.getenv("PORT", 8300))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-for-jwt-token-generation")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Redis
    REDIS_HOST: str = os.getenv("REDIS_HOST", "redis")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))
    
    # Service Discovery
    SERVICE_DISCOVERY_HOST: str = os.getenv("SERVICE_DISCOVERY_HOST", "service-discovery")
    SERVICE_DISCOVERY_PORT: int = int(os.getenv("SERVICE_DISCOVERY_PORT", 8000))
    
    # Frontend
    STATIC_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend/build")
    
    class Config:
        """Pydantic config class"""
        env_file = ".env"


# Create settings instance
settings = Settings()

# Configure logger
logger.remove()
logger.add(
    "dashboard_service.log",
    level=settings.LOG_LEVEL,
    rotation="10 MB",
    retention="1 week",
)
logger.add(lambda msg: print(msg, end=""), level=settings.LOG_LEVEL)

logger.info(f"Loaded configuration for {settings.APP_NAME} v{settings.APP_VERSION}")