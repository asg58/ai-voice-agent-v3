"""
Enhanced configuration management for Real-time Voice AI
Provides environment-aware settings with validation and security
"""
import os
from typing import List, Optional
from pathlib import Path

# Use simplified validation for now (will work without pydantic dependency)
class BaseSettings:
    """Base settings class with environment variable loading"""
    
    def __init__(self):
        self._load_from_env()
    
    def _load_from_env(self):
        """Load configuration from environment variables"""
        # Get all class attributes that are not private
        for attr_name in dir(self):
            if not attr_name.startswith('_') and hasattr(self, attr_name):
                env_value = os.getenv(attr_name.upper())
                if env_value is not None:
                    # Simple type conversion
                    current_value = getattr(self, attr_name)
                    if isinstance(current_value, bool):
                        setattr(self, attr_name, env_value.lower() in ('true', '1', 'yes', 'on'))
                    elif isinstance(current_value, int):
                        try:
                            setattr(self, attr_name, int(env_value))
                        except ValueError:
                            pass
                    elif isinstance(current_value, float):
                        try:
                            setattr(self, attr_name, float(env_value))
                        except ValueError:
                            pass
                    else:
                        setattr(self, attr_name, env_value)


class ServiceConfig(BaseSettings):
    """Service configuration with enhanced security and validation"""
      # === SERVICE SETTINGS ===
    service_name: str = "realtime-voice-ai"
    service_version: str = "1.0.0-alpha"
    service_host: str = "0.0.0.0"
    service_port: int = 8080  # Standardized port
    debug: bool = False
    log_level: str = "info"
    
    # === ENVIRONMENT ===
    environment: str = "development"  # development, staging, production
    
    # === SECURITY SETTINGS ===
    cors_origins: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]  # Restricted origins
    max_request_size: int = 100000  # 100KB
    enable_rate_limiting: bool = True
    api_key_required: bool = False  # Set to True in production
    
    # === SESSION MANAGEMENT ===
    max_sessions: int = 1000
    session_timeout_hours: int = 24
    inactive_session_timeout_minutes: int = 30
    session_cleanup_interval_seconds: int = 300
    
    # === WEBSOCKET SETTINGS ===
    websocket_ping_interval: int = 30
    websocket_ping_timeout: int = 10
    max_websocket_connections: int = 1000
    
    # === RATE LIMITING ===
    max_messages_per_minute: int = 60
    max_audio_messages_per_minute: int = 30
    rate_limit_window_seconds: int = 60
    
    # === AUDIO SETTINGS ===
    audio_sample_rate: int = 16000
    audio_channels: int = 1
    audio_chunk_size: int = 1024
    max_audio_message_size: int = 1000000  # 1MB
    
    # === VAD SETTINGS ===
    vad_threshold: float = 0.5
    vad_min_speech_duration: float = 0.25
    vad_max_silence_duration: float = 2.0
      # === LLM SETTINGS ===
    # OpenAI Configuration
    openai_api_key: str = ""
    openai_model: str = "gpt-3.5-turbo"
    openai_max_tokens: int = 256
    openai_temperature: float = 0.7
    
    # Ollama Configuration (alternative)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3"
    llama_timeout_seconds: int = 30
    max_context_length: int = 4000
    
    # === TTS SETTINGS ===
    tts_language: str = "nl"
    tts_speed: float = 1.0
    tts_model: str = "xtts_v2"
    
    # === DATABASE SETTINGS ===
    database_url: str = "sqlite:///./voice_ai.db"
    redis_url: str = "redis://localhost:6379/0"
    
    # === WEBRTC SETTINGS ===
    webrtc_ice_servers: List[str] = ["stun:stun.l.google.com:19302"]
    webrtc_audio_codec: str = "opus"
    
    # === MONITORING ===
    enable_metrics: bool = True
    metrics_port: int = 9090
    health_check_interval: int = 30
    
    # === LOGGING ===
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_file: Optional[str] = None
    max_log_file_size_mb: int = 10
    log_rotation_count: int = 5
    
    # === STORAGE ===
    storage_path: str = "./storage"
    temp_storage_path: str = "./storage/temp"
    
    def __init__(self):
        super().__init__()
        self._validate_config()
        self._setup_storage()
    
    def _validate_config(self):
        """Validate configuration values"""
        # Port validation
        if not (1 <= self.service_port <= 65535):
            raise ValueError(f"Invalid service_port: {self.service_port}")
        
        if not (1 <= self.metrics_port <= 65535):
            raise ValueError(f"Invalid metrics_port: {self.metrics_port}")
        
        # Audio validation
        if self.audio_sample_rate not in [8000, 16000, 22050, 44100, 48000]:
            raise ValueError(f"Unsupported audio_sample_rate: {self.audio_sample_rate}")
        
        if self.audio_channels not in [1, 2]:
            raise ValueError(f"Invalid audio_channels: {self.audio_channels}")
        
        # Rate limiting validation
        if self.max_messages_per_minute <= 0:
            raise ValueError("max_messages_per_minute must be positive")
        
        # Environment validation
        if self.environment not in ["development", "staging", "production"]:
            raise ValueError(f"Invalid environment: {self.environment}")
        
        # Production-specific validations
        if self.environment == "production":
            if self.debug:
                print("WARNING: Debug mode enabled in production!")
            
            if "*" in self.cors_origins:
                print("WARNING: CORS allows all origins in production!")
    
    def _setup_storage(self):
        """Create storage directories"""
        Path(self.storage_path).mkdir(parents=True, exist_ok=True)
        Path(self.temp_storage_path).mkdir(parents=True, exist_ok=True)
    
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment == "production"
    
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.environment == "development"
    
    def get_log_config(self) -> dict:
        """Get logging configuration"""
        config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": self.log_format,
                },
            },
            "handlers": {
                "default": {
                    "formatter": "default",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                },
            },
            "root": {
                "level": self.log_level.upper(),
                "handlers": ["default"],
            },
        }
        
        # Add file handler if log_file is specified
        if self.log_file:
            config["handlers"]["file"] = {
                "formatter": "default",
                "class": "logging.handlers.RotatingFileHandler",
                "filename": self.log_file,
                "maxBytes": self.max_log_file_size_mb * 1024 * 1024,
                "backupCount": self.log_rotation_count,
            }
            config["root"]["handlers"].append("file")
        
        return config
    
    def get_cors_config(self) -> dict:
        """Get CORS configuration"""
        return {
            "allow_origins": self.cors_origins,
            "allow_credentials": True,
            "allow_methods": ["*"],
            "allow_headers": ["*"],
        }
    
    def get_rate_limit_config(self) -> dict:
        """Get rate limiting configuration"""
        return {
            "enabled": self.enable_rate_limiting,
            "max_messages_per_minute": self.max_messages_per_minute,
            "max_audio_per_minute": self.max_audio_messages_per_minute,
            "window_seconds": self.rate_limit_window_seconds,
        }


class SecurityConfig:
    """Security-specific configuration"""
    
    # JWT settings (for future authentication)
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production")
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    
    # API key settings (for future API access)
    api_key_header: str = "X-API-Key"
    require_api_key: bool = False
    
    # Content security
    max_message_length: int = 5000
    max_audio_duration_seconds: int = 30
    allowed_file_types: List[str] = ["wav", "mp3", "ogg", "webm"]
    
    # Network security
    trusted_proxies: List[str] = ["127.0.0.1", "::1"]
    enable_csrf_protection: bool = True
    
    def __init__(self):
        if os.getenv("REQUIRE_API_KEY", "").lower() == "true":
            self.require_api_key = True


# Load configuration
try:
    # Try to load from .env file
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Create global configuration instances
settings = ServiceConfig()
security_settings = SecurityConfig()

# Export commonly used settings
SERVICE_HOST = settings.service_host
SERVICE_PORT = settings.service_port
DEBUG = settings.debug
ENVIRONMENT = settings.environment
