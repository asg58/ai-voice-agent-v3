"""
Configuration settings for the Real-time Voice AI Service
"""
import os
from typing import List, Dict, Any, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application settings"""
    
    # Application info
    APP_NAME: str = "Real-time Voice AI Service"
    APP_DESCRIPTION: str = "AI Voice Agent with real-time audio processing capabilities"
    APP_VERSION: str = "1.0.0"
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8080
    WORKERS: int = 1
    
    # CORS
    CORS_ORIGINS: List[str] = ["*"]
    
    # Metrics
    ENABLE_METRICS: bool = True
    
    # Audio settings
    SAMPLE_RATE: int = 16000
    CHANNELS: int = 1
    
    # Speech-to-Text settings
    STT_MODEL: str = "whisper-1"
    STT_LANGUAGE: Optional[str] = None  # Auto-detect if None
    
    # Text-to-Speech settings
    TTS_MODEL: str = "tts-1"
    TTS_VOICE: str = "alloy"
    
    # OpenAI settings
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4"
    
    # Redis settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    
    # Database settings
    DATABASE_URL: str = "sqlite:///./voice_service.db"
    
    # Storage settings
    STORAGE_PATH: str = "./storage"
    
    # Service discovery settings
    SERVICE_DISCOVERY_URL: str = "http://service-discovery:8000"
    
    # Model config
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

# Create settings instance
settings = Settings()