"""
Voice Module Configuration Settings

Configuration management for the Voice Module service using Pydantic settings.
"""

import os
from typing import List, Optional
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Voice Module service configuration."""

    # Application settings
    APP_NAME: str = "Voice Module Service"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False, env="DEBUG")
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")

    # Server settings
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8001, env="PORT")

    # Voice Processing settings
    WHISPER_MODEL: str = Field(default="base", env="WHISPER_MODEL")  # tiny, base, small, medium, large
    WHISPER_DEVICE: str = Field(default="cpu", env="WHISPER_DEVICE")  # cpu, cuda
    WHISPER_LANGUAGE: Optional[str] = Field(default=None, env="WHISPER_LANGUAGE")  # auto-detect if None

    # Audio settings
    SAMPLE_RATE: int = Field(default=16000, env="VOICE_SAMPLE_RATE")
    CHUNK_SIZE: int = Field(default=1024, env="VOICE_CHUNK_SIZE")
    CHANNELS: int = Field(default=1, env="VOICE_CHANNELS")
    AUDIO_FORMAT: str = Field(default="wav", env="AUDIO_FORMAT")

    # Voice Activity Detection
    VAD_ENABLED: bool = Field(default=True, env="VAD_ENABLED")
    VAD_THRESHOLD: float = Field(default=0.5, env="VAD_THRESHOLD")
    SILENCE_THRESHOLD: float = Field(default=0.1, env="VOICE_SILENCE_THRESHOLD")
    SILENCE_DURATION: float = Field(default=2.0, env="VOICE_SILENCE_DURATION")

    # Processing limits
    MAX_AUDIO_LENGTH: int = Field(default=30, env="MAX_AUDIO_LENGTH")  # seconds
    MAX_FILE_SIZE: int = Field(default=25 * 1024 * 1024, env="MAX_FILE_SIZE")  # 25MB
    PROCESSING_TIMEOUT: int = Field(default=30, env="VOICE_TIMEOUT")

    # TTS settings
    TTS_ENABLED: bool = Field(default=True, env="TTS_ENABLED")
    TTS_MODEL: str = Field(default="tts-1", env="TTS_MODEL")
    TTS_VOICE: str = Field(default="alloy", env="TTS_VOICE")  # alloy, echo, fable, onyx, nova, shimmer
    TTS_SPEED: float = Field(default=1.0, env="TTS_SPEED")

    # External services
    OPENAI_API_KEY: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    CORE_ENGINE_URL: str = Field(default="http://localhost:8000", env="CORE_ENGINE_URL")

    # Storage settings
    AUDIO_STORAGE_PATH: str = Field(default="./storage/audio", env="AUDIO_STORAGE_PATH")
    TEMP_STORAGE_PATH: str = Field(default="./storage/temp", env="TEMP_STORAGE_PATH")
    CLEANUP_TEMP_FILES: bool = Field(default=True, env="CLEANUP_TEMP_FILES")

    # Security settings
    SECRET_KEY: str = Field(default="your-secret-key-here", env="SECRET_KEY")
    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        env="ALLOWED_ORIGINS"
    )

    # Logging settings
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    ENABLE_JSON_LOGGING: bool = Field(default=True, env="ENABLE_JSON_LOGGING")
    LOG_FILE: Optional[str] = Field(default=None, env="LOG_FILE")

    # Monitoring settings
    ENABLE_METRICS: bool = Field(default=True, env="ENABLE_METRICS")
    METRICS_PORT: int = Field(default=9091, env="METRICS_PORT")

    # WebSocket settings
    MAX_CONNECTIONS: int = Field(default=100, env="MAX_WS_CONNECTIONS")
    HEARTBEAT_INTERVAL: int = Field(default=30, env="WS_HEARTBEAT_INTERVAL")

    # Real-time processing
    REAL_TIME_PROCESSING: bool = Field(default=True, env="REAL_TIME_PROCESSING")
    STREAMING_ENABLED: bool = Field(default=True, env="STREAMING_ENABLED")
    BUFFER_SIZE: int = Field(default=4096, env="BUFFER_SIZE")

    # Language support
    SUPPORTED_LANGUAGES: List[str] = Field(
        default=[
            "en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh",
            "ar", "hi", "nl", "pl", "tr", "sv", "da", "no", "fi"
        ],
        env="SUPPORTED_LANGUAGES"
    )

    # Performance settings
    MAX_CONCURRENT_REQUESTS: int = Field(default=10, env="MAX_CONCURRENT_REQUESTS")
    PROCESSING_POOL_SIZE: int = Field(default=4, env="PROCESSING_POOL_SIZE")

    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get settings instance for dependency injection."""
    return settings