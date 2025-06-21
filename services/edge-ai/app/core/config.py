"""
Configuration settings for Edge AI Service
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
    """
    APP_NAME: str = "Edge AI Service"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    PORT: int = int(os.getenv("PORT", 8500))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    class Config:
        """Pydantic config class"""
        env_file = ".env"


# Create settings instance
settings = Settings()

# Configure logger
logger.remove()
logger.add(
    "edge_ai_service.log",
    level=settings.LOG_LEVEL.upper(),
    rotation="10 MB",
    retention="1 week",
)
logger.add(lambda msg: print(msg, end=""), level=settings.LOG_LEVEL.upper())

logger.info(f"Loaded configuration for {settings.APP_NAME} v{settings.APP_VERSION}")