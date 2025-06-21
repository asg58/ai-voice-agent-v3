"""
Input validation utilities for Real-time Voice AI
Provides secure validation for WebSocket messages and API inputs
"""
from typing import Dict, Any, Optional, Literal
from pydantic import BaseModel, Field, ValidationError
import json
import logging
import time

logger = logging.getLogger(__name__)


class WebSocketMessageBase(BaseModel):
    """Base WebSocket message with common fields"""
    type: str = Field(..., min_length=1, max_length=50)
    session_id: str = Field(..., min_length=1, max_length=100)
    timestamp: Optional[str] = None


class PingMessage(WebSocketMessageBase):
    """Ping message validation"""
    type: Literal["ping"] = "ping"


class TextMessage(WebSocketMessageBase):
    """Text message validation"""
    type: Literal["text_message"] = Field(default="text_message", description="Message type identifier")
    text: str = Field(..., min_length=1, max_length=5000, description="Text content")


class AudioDataMessage(WebSocketMessageBase):
    """Audio data message validation"""
    type: Literal["audio_data"] = Field(default="audio_data", description="Message type identifier")
    audio_data: str = Field(..., min_length=1, max_length=1000000, description="Base64 encoded audio data")
    sample_rate: int = Field(default=16000, ge=8000, le=48000, description="Audio sample rate")
    channels: int = Field(default=1, ge=1, le=2, description="Number of audio channels")


class StatusRequestMessage(WebSocketMessageBase):
    """Status request message validation"""
    type: Literal["status_request"] = Field(default="status_request", description="Message type identifier")


class SessionCreateRequest(BaseModel):
    """Session creation request validation"""
    user_id: Optional[str] = Field(None, max_length=100)


# Message type mapping for validation
MESSAGE_VALIDATORS = {
    "ping": PingMessage,
    "text_message": TextMessage,
    "audio_data": AudioDataMessage,
    "status_request": StatusRequestMessage,
}


class InputValidator:
    """Secure input validation for WebSocket messages"""
    
    @staticmethod
    def validate_json(data: str, max_size: int = 100000) -> Optional[Dict[str, Any]]:
        """
        Safely parse and validate JSON data
        
        Args:
            data: JSON string to parse
            max_size: Maximum allowed size in bytes
            
        Returns:
            Parsed JSON data or None if invalid
        """
        # Check size limit
        if len(data.encode('utf-8')) > max_size:
            logger.warning(f"JSON data too large: {len(data)} bytes")
            return None
        
        try:
            parsed = json.loads(data)
            
            # Basic structure validation
            if not isinstance(parsed, dict):
                logger.warning("JSON data is not an object")
                return None
                
            return parsed
            
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON data: {e}")
            return None
        except (UnicodeDecodeError, MemoryError) as e:
            logger.error(f"Error processing JSON data: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error parsing JSON: {e}")
            return None
    
    @staticmethod
    def validate_websocket_message(data: Dict[str, Any]) -> Optional[WebSocketMessageBase]:
        """
        Validate WebSocket message against schema
        
        Args:
            data: Parsed JSON data
            
        Returns:
            Validated message object or None if invalid
        """
        try:
            # Check required type field
            message_type = data.get("type")
            if not message_type:
                logger.warning("Missing 'type' field in message")
                return None
            
            # Get appropriate validator
            validator_class = MESSAGE_VALIDATORS.get(message_type)
            if not validator_class:
                logger.warning(f"Unknown message type: {message_type}")
                return None
            
            # Validate against schema
            validated_message = validator_class(**data)
            return validated_message
            
        except ValidationError as e:
            logger.warning(f"Message validation failed: {e}")
            return None
        except (KeyError, TypeError) as e:
            logger.warning(f"Invalid message structure: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected validation error: {e}")
            return None
    
    @staticmethod
    def validate_session_create(data: Dict[str, Any]) -> Optional[SessionCreateRequest]:
        """
        Validate session creation request
        
        Args:
            data: Request data
            
        Returns:
            Validated request or None if invalid
        """
        try:
            validated_request = SessionCreateRequest(**data)
            return validated_request
        except ValidationError as e:
            logger.warning(f"Session creation validation failed: {e}")
            return None
        except (KeyError, TypeError) as e:
            logger.warning(f"Invalid session creation data structure: {e}")
            return None
    
    @staticmethod
    def sanitize_string(text: str, max_length: int = 1000) -> str:
        """
        Sanitize string input for safe processing
        
        Args:
            text: Input string
            max_length: Maximum allowed length
            
        Returns:
            Sanitized string
        """
        if not isinstance(text, str):
            return ""
        
        # Truncate if too long
        if len(text) > max_length:
            text = text[:max_length]
        
        # Remove null bytes and control characters (except newlines/tabs)
        sanitized = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t')
        
        return sanitized.strip()


class RateLimiter:
    """Rate limiting implementation with Redis backend"""
    
    def __init__(self):
        self.local_cache = {}  # Fallback for when Redis is unavailable
    
    def check_rate_limit(self, session_id: str, message_type: str, limit: int, window: int = 60) -> bool:
        """
        Check if request is within rate limits
        
        Args:
            session_id: Session identifier
            message_type: Type of message being sent
            limit: Maximum requests per window
            window: Time window in seconds
            
        Returns:
            True if within limits, False otherwise
        """
        # For now, use simple local cache (TODO: implement Redis)
        key = f"{session_id}:{message_type}"
        current_time = int(time.time())
        
        if key not in self.local_cache:
            self.local_cache[key] = []
        
        # Clean old entries
        self.local_cache[key] = [
            timestamp for timestamp in self.local_cache[key]
            if current_time - timestamp < window
        ]
        
        # Check limit
        if len(self.local_cache[key]) >= limit:
            logger.warning(f"Rate limit exceeded for session {session_id}, type {message_type}")
            return False
        
        # Add current request
        self.local_cache[key].append(current_time)
        return True


class SecurityLimits:
    """Security limits and constants"""
    
    # Message size limits
    MAX_JSON_SIZE = 100000  # 100KB
    MAX_TEXT_MESSAGE_LENGTH = 5000
    MAX_AUDIO_DATA_SIZE = 1000000  # 1MB base64 encoded
    
    # Rate limits (per session per minute)
    MAX_MESSAGES_PER_MINUTE = 60
    MAX_AUDIO_MESSAGES_PER_MINUTE = 30
    
    # Session limits
    MAX_SESSIONS_PER_IP = 10
    MAX_SESSION_DURATION_HOURS = 24


# Global validator instance
input_validator = InputValidator()
rate_limiter = RateLimiter()


def validate_message(raw_data: str) -> Optional[WebSocketMessageBase]:
    """
    Complete message validation pipeline
    
    Args:
        raw_data: Raw WebSocket message data
        
    Returns:
        Validated message or None if invalid
    """
    # Parse JSON
    json_data = input_validator.validate_json(raw_data, SecurityLimits.MAX_JSON_SIZE)
    if json_data is None:
        return None
    
    # Validate message structure
    validated_message = input_validator.validate_websocket_message(json_data)
    return validated_message
