"""
Configuration settings for the Event Broker Service
"""
import os
from typing import List, Dict, Any, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application settings"""
    
    # Application info
    APP_NAME: str = "Event Broker"
    APP_DESCRIPTION: str = "Event Broker for the AI Voice Agent platform"
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

    # RabbitMQ settings
    RABBITMQ_HOST: str = "rabbitmq"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = "guest"
    RABBITMQ_PASSWORD: str = "guest"
    RABBITMQ_VHOST: str = "/"

    # Connection settings
    CONNECTION_RETRY_DELAY: int = 5
    CONNECTION_MAX_RETRIES: int = 10

    # Exchange settings
    DEFAULT_EXCHANGE: str = "events"
    DEFAULT_EXCHANGE_TYPE: str = "topic"

    # Queue settings
    QUEUE_TTL: int = 86400000  # 24 hours in milliseconds
    QUEUE_MAX_LENGTH: int = 10000

    # Dead letter settings
    DEAD_LETTER_EXCHANGE: str = "dead_letters"

    # Worker settings
    WORKER_PREFETCH_COUNT: int = 10
    WORKER_POOL_SIZE: int = 5

    # Service discovery settings
    SERVICE_DISCOVERY_URL: str = "http://service-discovery:8000"

    # Event schema validation
    SCHEMA_VALIDATION_ENABLED: bool = True

    # Predefined queues and routing keys
    PREDEFINED_QUEUES: Dict[str, Dict[str, Any]] = {
        "voice_events": {
            "routing_key": "events.voice.*",
            "durable": True,
            "auto_delete": False
        },
        "user_events": {
            "routing_key": "events.user.*",
            "durable": True,
            "auto_delete": False
        },
        "system_events": {
            "routing_key": "events.system.*",
            "durable": True,
            "auto_delete": False
        },
        "notification_events": {
            "routing_key": "events.notification.*",
            "durable": True,
            "auto_delete": False
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