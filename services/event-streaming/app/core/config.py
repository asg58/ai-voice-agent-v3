"""
Configuration settings for the Event Streaming service.
"""
import os
from typing import List, Dict, Any, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    """
    Event Streaming configuration settings.
    """
    # API settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "AI Voice Agent Event Streaming"
    DEBUG: bool = Field(default=False)
    
    # CORS settings
    CORS_ORIGINS: List[str] = Field(default=["*"])
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    
    # Kafka settings
    KAFKA_BOOTSTRAP_SERVERS: str = Field(default="kafka:9092", env="KAFKA_BOOTSTRAP_SERVERS")
    KAFKA_CONSUMER_GROUP: str = Field(default="event-streaming-group", env="KAFKA_CONSUMER_GROUP")
    KAFKA_AUTO_OFFSET_RESET: str = Field(default="earliest", env="KAFKA_AUTO_OFFSET_RESET")
    KAFKA_ENABLE_AUTO_COMMIT: bool = Field(default=True, env="KAFKA_ENABLE_AUTO_COMMIT")
    KAFKA_AUTO_COMMIT_INTERVAL_MS: int = Field(default=5000, env="KAFKA_AUTO_COMMIT_INTERVAL_MS")
    KAFKA_SESSION_TIMEOUT_MS: int = Field(default=30000, env="KAFKA_SESSION_TIMEOUT_MS")
    KAFKA_MAX_POLL_INTERVAL_MS: int = Field(default=300000, env="KAFKA_MAX_POLL_INTERVAL_MS")
    KAFKA_MAX_POLL_RECORDS: int = Field(default=500, env="KAFKA_MAX_POLL_RECORDS")
    
    # Schema Registry settings
    SCHEMA_REGISTRY_URL: str = Field(default="http://schema-registry:8081", env="SCHEMA_REGISTRY_URL")
    
    # Connection settings
    CONNECTION_RETRY_DELAY: int = Field(default=5, env="CONNECTION_RETRY_DELAY")
    CONNECTION_MAX_RETRIES: int = Field(default=10, env="CONNECTION_MAX_RETRIES")
    
    # Worker settings
    WORKER_POOL_SIZE: int = Field(default=5, env="WORKER_POOL_SIZE")
    
    # Logging settings
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Service discovery settings
    SERVICE_DISCOVERY_URL: str = Field(default="http://service-discovery:8000", env="SERVICE_DISCOVERY_URL")
    
    # Event schema validation
    SCHEMA_VALIDATION_ENABLED: bool = Field(default=True, env="SCHEMA_VALIDATION_ENABLED")
    
    # Predefined topics
    PREDEFINED_TOPICS: Dict[str, Dict[str, Any]] = {
        "voice-events": {
            "partitions": 3,
            "replication_factor": 1,
            "config": {
                "retention.ms": 604800000,  # 7 days
                "cleanup.policy": "delete"
            }
        },
        "user-events": {
            "partitions": 3,
            "replication_factor": 1,
            "config": {
                "retention.ms": 604800000,  # 7 days
                "cleanup.policy": "delete"
            }
        },
        "system-events": {
            "partitions": 3,
            "replication_factor": 1,
            "config": {
                "retention.ms": 604800000,  # 7 days
                "cleanup.policy": "delete"
            }
        },
        "notification-events": {
            "partitions": 3,
            "replication_factor": 1,
            "config": {
                "retention.ms": 604800000,  # 7 days
                "cleanup.policy": "delete"
            }
        },
        "analytics-events": {
            "partitions": 3,
            "replication_factor": 1,
            "config": {
                "retention.ms": 2592000000,  # 30 days
                "cleanup.policy": "delete"
            }
        }
    }
    
    # Stream processing configurations
    STREAM_PROCESSING_ENABLED: bool = Field(default=True, env="STREAM_PROCESSING_ENABLED")
    STREAM_PROCESSING_WINDOW_SIZE_MS: int = Field(default=60000, env="STREAM_PROCESSING_WINDOW_SIZE_MS")  # 1 minute
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True
    )

# Create global settings object
settings = Settings()