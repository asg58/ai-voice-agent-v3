"""
Base Configuration Settings

This module defines base configuration settings that are shared
across all services in the AI Voice Agent platform.
"""

import os
from typing import List, Optional, Dict, Any
from pydantic_settings import BaseSettings
from pydantic import Field, validator


class BaseServiceSettings(BaseSettings):
    """Base configuration settings for all services."""
    
    # Environment
    ENVIRONMENT: str = Field(default="development", description="Environment (development, staging, production)")
    DEBUG: bool = Field(default=False, description="Debug mode")
    
    # Service information
    SERVICE_NAME: str = Field(..., description="Service name")
    SERVICE_VERSION: str = Field(default="1.0.0", description="Service version")
    
    # API configuration
    API_HOST: str = Field(default="0.0.0.0", description="API host")
    API_PORT: int = Field(default=8000, description="API port")
    API_PREFIX: str = Field(default="/api/v1", description="API prefix")
    
    # CORS configuration
    ALLOWED_ORIGINS: List[str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:8080",
            "http://localhost:3001"
        ],
        description="Allowed CORS origins"
    )
    ALLOWED_METHODS: List[str] = Field(
        default=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        description="Allowed HTTP methods"
    )
    ALLOWED_HEADERS: List[str] = Field(
        default=["*"],
        description="Allowed headers"
    )
    
    # Database configuration
    DATABASE_URL: str = Field(
        default="postgresql://user:password@localhost:5432/ai_voice_agent",
        description="Database connection URL"
    )
    DATABASE_POOL_SIZE: int = Field(default=10, description="Database connection pool size")
    DATABASE_MAX_OVERFLOW: int = Field(default=20, description="Database max overflow connections")
    
    # Redis configuration
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )
    REDIS_POOL_SIZE: int = Field(default=10, description="Redis connection pool size")
    REDIS_TTL: int = Field(default=3600, description="Default Redis TTL in seconds")
    
    # Security configuration
    SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production",
        description="Secret key for JWT tokens and encryption"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        description="Access token expiration time in minutes"
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=7,
        description="Refresh token expiration time in days"
    )
    
    # Logging configuration
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format"
    )
    ENABLE_JSON_LOGGING: bool = Field(default=True, description="Enable JSON logging format")
    LOG_FILE: Optional[str] = Field(None, description="Log file path")
    
    # Monitoring configuration
    ENABLE_METRICS: bool = Field(default=True, description="Enable Prometheus metrics")
    METRICS_PORT: int = Field(default=9090, description="Metrics port")
    ENABLE_TRACING: bool = Field(default=False, description="Enable distributed tracing")
    JAEGER_ENDPOINT: Optional[str] = Field(None, description="Jaeger tracing endpoint")
    
    # Rate limiting
    RATE_LIMIT_ENABLED: bool = Field(default=True, description="Enable rate limiting")
    RATE_LIMIT_REQUESTS: int = Field(default=100, description="Rate limit requests per minute")
    RATE_LIMIT_WINDOW: int = Field(default=60, description="Rate limit window in seconds")
    
    # Health check configuration
    HEALTH_CHECK_INTERVAL: int = Field(default=30, description="Health check interval in seconds")
    HEALTH_CHECK_TIMEOUT: int = Field(default=10, description="Health check timeout in seconds")
    
    # External services
    EXTERNAL_SERVICES: Dict[str, str] = Field(
        default={
            "core_engine": "http://core-engine:8000",
            "voice_module": "http://voice-module:8001",
            "document_module": "http://document-module:8002",
            "api_gateway": "http://api-gateway:8080",
            "dashboard": "http://dashboard:3000"
        },
        description="External service URLs"
    )
    
    @validator('ENVIRONMENT')
    def validate_environment(cls, v):
        """Validate environment value."""
        allowed_environments = ['development', 'staging', 'production']
        if v not in allowed_environments:
            raise ValueError(f'Environment must be one of: {allowed_environments}')
        return v
    
    @validator('LOG_LEVEL')
    def validate_log_level(cls, v):
        """Validate log level value."""
        allowed_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in allowed_levels:
            raise ValueError(f'Log level must be one of: {allowed_levels}')
        return v.upper()
    
    @validator('SECRET_KEY')
    def validate_secret_key(cls, v, values):
        """Validate secret key in production."""
        if values.get('ENVIRONMENT') == 'production' and v == 'your-secret-key-change-in-production':
            raise ValueError('SECRET_KEY must be changed in production environment')
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


class DatabaseSettings(BaseSettings):
    """Database-specific configuration settings."""
    
    DATABASE_URL: str = Field(..., description="Database connection URL")
    DATABASE_POOL_SIZE: int = Field(default=10, description="Connection pool size")
    DATABASE_MAX_OVERFLOW: int = Field(default=20, description="Max overflow connections")
    DATABASE_POOL_TIMEOUT: int = Field(default=30, description="Pool timeout in seconds")
    DATABASE_POOL_RECYCLE: int = Field(default=3600, description="Pool recycle time in seconds")
    DATABASE_ECHO: bool = Field(default=False, description="Enable SQL query logging")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


class RedisSettings(BaseSettings):
    """Redis-specific configuration settings."""
    
    REDIS_URL: str = Field(..., description="Redis connection URL")
    REDIS_POOL_SIZE: int = Field(default=10, description="Connection pool size")
    REDIS_TTL: int = Field(default=3600, description="Default TTL in seconds")
    REDIS_TIMEOUT: int = Field(default=5, description="Connection timeout in seconds")
    REDIS_RETRY_ON_TIMEOUT: bool = Field(default=True, description="Retry on timeout")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


class SecuritySettings(BaseSettings):
    """Security-specific configuration settings."""
    
    SECRET_KEY: str = Field(..., description="Secret key for encryption")
    ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, description="Access token expiry")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, description="Refresh token expiry")
    
    # Password hashing
    BCRYPT_ROUNDS: int = Field(default=12, description="Bcrypt hashing rounds")
    
    # API Key configuration
    API_KEY_HEADER: str = Field(default="X-API-Key", description="API key header name")
    REQUIRE_API_KEY: bool = Field(default=False, description="Require API key for all requests")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


def get_settings(service_name: str) -> BaseServiceSettings:
    """
    Get configuration settings for a specific service.
    
    Args:
        service_name: Name of the service
        
    Returns:
        BaseServiceSettings instance with service-specific configuration
    """
    return BaseServiceSettings(SERVICE_NAME=service_name)


def load_config_from_file(file_path: str) -> Dict[str, Any]:
    """
    Load configuration from a file.
    
    Args:
        file_path: Path to configuration file
        
    Returns:
        Dictionary containing configuration
    """
    import json
    import yaml
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Configuration file not found: {file_path}")
    
    file_extension = os.path.splitext(file_path)[1].lower()
    
    with open(file_path, 'r') as f:
        if file_extension == '.json':
            return json.load(f)
        elif file_extension in ['.yml', '.yaml']:
            return yaml.safe_load(f)
        else:
            raise ValueError(f"Unsupported configuration file format: {file_extension}")


# Export main classes and functions
__all__ = [
    'BaseServiceSettings',
    'DatabaseSettings',
    'RedisSettings',
    'SecuritySettings',
    'get_settings',
    'load_config_from_file'
]"""
Base Configuration Settings

This module defines base configuration settings that are shared
across all services in the AI Voice Agent platform.
"""

import os
from typing import List, Optional, Dict, Any
from pydantic_settings import BaseSettings
from pydantic import Field, validator


class BaseServiceSettings(BaseSettings):
    """Base configuration settings for all services."""
    
    # Environment
    ENVIRONMENT: str = Field(default="development", description="Environment (development, staging, production)")
    DEBUG: bool = Field(default=False, description="Debug mode")
    
    # Service information
    SERVICE_NAME: str = Field(..., description="Service name")
    SERVICE_VERSION: str = Field(default="1.0.0", description="Service version")
    
    # API configuration
    API_HOST: str = Field(default="0.0.0.0", description="API host")
    API_PORT: int = Field(default=8000, description="API port")
    API_PREFIX: str = Field(default="/api/v1", description="API prefix")
    
    # CORS configuration
    ALLOWED_ORIGINS: List[str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:8080",
            "http://localhost:3001"
        ],
        description="Allowed CORS origins"
    )
    ALLOWED_METHODS: List[str] = Field(
        default=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        description="Allowed HTTP methods"
    )
    ALLOWED_HEADERS: List[str] = Field(
        default=["*"],
        description="Allowed headers"
    )
    
    # Database configuration
    DATABASE_URL: str = Field(
        default="postgresql://user:password@localhost:5432/ai_voice_agent",
        description="Database connection URL"
    )
    DATABASE_POOL_SIZE: int = Field(default=10, description="Database connection pool size")
    DATABASE_MAX_OVERFLOW: int = Field(default=20, description="Database max overflow connections")
    
    # Redis configuration
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )
    REDIS_POOL_SIZE: int = Field(default=10, description="Redis connection pool size")
    REDIS_TTL: int = Field(default=3600, description="Default Redis TTL in seconds")
    
    # Security configuration
    SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production",
        description="Secret key for JWT tokens and encryption"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        description="Access token expiration time in minutes"
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=7,
        description="Refresh token expiration time in days"
    )
    
    # Logging configuration
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format"
    )
    ENABLE_JSON_LOGGING: bool = Field(default=True, description="Enable JSON logging format")
    LOG_FILE: Optional[str] = Field(None, description="Log file path")
    
    # Monitoring configuration
    ENABLE_METRICS: bool = Field(default=True, description="Enable Prometheus metrics")
    METRICS_PORT: int = Field(default=9090, description="Metrics port")
    ENABLE_TRACING: bool = Field(default=False, description="Enable distributed tracing")
    JAEGER_ENDPOINT: Optional[str] = Field(None, description="Jaeger tracing endpoint")
    
    # Rate limiting
    RATE_LIMIT_ENABLED: bool = Field(default=True, description="Enable rate limiting")
    RATE_LIMIT_REQUESTS: int = Field(default=100, description="Rate limit requests per minute")
    RATE_LIMIT_WINDOW: int = Field(default=60, description="Rate limit window in seconds")
    
    # Health check configuration
    HEALTH_CHECK_INTERVAL: int = Field(default=30, description="Health check interval in seconds")
    HEALTH_CHECK_TIMEOUT: int = Field(default=10, description="Health check timeout in seconds")
    
    # External services
    EXTERNAL_SERVICES: Dict[str, str] = Field(
        default={
            "core_engine": "http://core-engine:8000",
            "voice_module": "http://voice-module:8001",
            "document_module": "http://document-module:8002",
            "api_gateway": "http://api-gateway:8080",
            "dashboard": "http://dashboard:3000"
        },
        description="External service URLs"
    )
    
    @validator('ENVIRONMENT')
    def validate_environment(cls, v):
        """Validate environment value."""
        allowed_environments = ['development', 'staging', 'production']
        if v not in allowed_environments:
            raise ValueError(f'Environment must be one of: {allowed_environments}')
        return v
    
    @validator('LOG_LEVEL')
    def validate_log_level(cls, v):
        """Validate log level value."""
        allowed_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in allowed_levels:
            raise ValueError(f'Log level must be one of: {allowed_levels}')
        return v.upper()
    
    @validator('SECRET_KEY')
    def validate_secret_key(cls, v, values):
        """Validate secret key in production."""
        if values.get('ENVIRONMENT') == 'production' and v == 'your-secret-key-change-in-production':
            raise ValueError('SECRET_KEY must be changed in production environment')
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


class DatabaseSettings(BaseSettings):
    """Database-specific configuration settings."""
    
    DATABASE_URL: str = Field(..., description="Database connection URL")
    DATABASE_POOL_SIZE: int = Field(default=10, description="Connection pool size")
    DATABASE_MAX_OVERFLOW: int = Field(default=20, description="Max overflow connections")
    DATABASE_POOL_TIMEOUT: int = Field(default=30, description="Pool timeout in seconds")
    DATABASE_POOL_RECYCLE: int = Field(default=3600, description="Pool recycle time in seconds")
    DATABASE_ECHO: bool = Field(default=False, description="Enable SQL query logging")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


class RedisSettings(BaseSettings):
    """Redis-specific configuration settings."""
    
    REDIS_URL: str = Field(..., description="Redis connection URL")
    REDIS_POOL_SIZE: int = Field(default=10, description="Connection pool size")
    REDIS_TTL: int = Field(default=3600, description="Default TTL in seconds")
    REDIS_TIMEOUT: int = Field(default=5, description="Connection timeout in seconds")
    REDIS_RETRY_ON_TIMEOUT: bool = Field(default=True, description="Retry on timeout")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


class SecuritySettings(BaseSettings):
    """Security-specific configuration settings."""
    
    SECRET_KEY: str = Field(..., description="Secret key for encryption")
    ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, description="Access token expiry")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, description="Refresh token expiry")
    
    # Password hashing
    BCRYPT_ROUNDS: int = Field(default=12, description="Bcrypt hashing rounds")
    
    # API Key configuration
    API_KEY_HEADER: str = Field(default="X-API-Key", description="API key header name")
    REQUIRE_API_KEY: bool = Field(default=False, description="Require API key for all requests")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


def get_settings(service_name: str) -> BaseServiceSettings:
    """
    Get configuration settings for a specific service.
    
    Args:
        service_name: Name of the service
        
    Returns:
        BaseServiceSettings instance with service-specific configuration
    """
    return BaseServiceSettings(SERVICE_NAME=service_name)


def load_config_from_file(file_path: str) -> Dict[str, Any]:
    """
    Load configuration from a file.
    
    Args:
        file_path: Path to configuration file
        
    Returns:
        Dictionary containing configuration
    """
    import json
    import yaml
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Configuration file not found: {file_path}")
    
    file_extension = os.path.splitext(file_path)[1].lower()
    
    with open(file_path, 'r') as f:
        if file_extension == '.json':
            return json.load(f)
        elif file_extension in ['.yml', '.yaml']:
            return yaml.safe_load(f)
        else:
            raise ValueError(f"Unsupported configuration file format: {file_extension}")


# Export main classes and functions
__all__ = [
    'BaseServiceSettings',
    'DatabaseSettings',
    'RedisSettings',
    'SecuritySettings',
    'get_settings',
    'load_config_from_file'
]