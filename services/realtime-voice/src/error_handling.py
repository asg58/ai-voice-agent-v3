"""
Enhanced error handling for Real-time Voice AI
Provides structured error responses and logging
"""
import logging
import traceback
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum


class ErrorCode(Enum):
    """Standardized error codes"""
    # Client errors (4xx)
    INVALID_JSON = "INVALID_JSON"
    INVALID_MESSAGE_TYPE = "INVALID_MESSAGE_TYPE"
    MESSAGE_VALIDATION_FAILED = "MESSAGE_VALIDATION_FAILED"
    SESSION_NOT_FOUND = "SESSION_NOT_FOUND"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    
    # Server errors (5xx)
    INTERNAL_ERROR = "INTERNAL_ERROR"
    WEBSOCKET_ERROR = "WEBSOCKET_ERROR"
    PROCESSING_ERROR = "PROCESSING_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"


class ErrorResponse:
    """Structured error response"""
    
    def __init__(self, 
                 error_code: ErrorCode,
                 message: str,
                 session_id: Optional[str] = None,
                 details: Optional[Dict[str, Any]] = None):
        self.error_code = error_code
        self.message = message
        self.session_id = session_id
        self.details = details or {}
        self.timestamp = datetime.now().isoformat()
        
        # Generate correlation ID for tracking
        import uuid
        self.correlation_id = str(uuid.uuid4())[:8]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON response"""
        return {
            "type": "error",
            "error_code": self.error_code.value,
            "error_message": self.message,
            "session_id": self.session_id,
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp,
            "details": self.details
        }
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        import json
        return json.dumps(self.to_dict())


class ErrorHandler:
    """Enhanced error handling with logging and monitoring"""
    
    def __init__(self, logger_name: str = __name__):
        self.logger = logging.getLogger(logger_name)
    
    def handle_validation_error(self, 
                               session_id: Optional[str] = None,
                               details: Optional[str] = None) -> ErrorResponse:
        """Handle input validation errors"""
        error = ErrorResponse(
            error_code=ErrorCode.MESSAGE_VALIDATION_FAILED,
            message="Message validation failed",
            session_id=session_id,
            details={"validation_error": details} if details else None
        )
        
        self.logger.warning(f"Validation error [{error.correlation_id}]: {details}")
        return error
    
    def handle_json_error(self, 
                         session_id: Optional[str] = None,
                         details: Optional[str] = None) -> ErrorResponse:
        """Handle JSON parsing errors"""
        error = ErrorResponse(
            error_code=ErrorCode.INVALID_JSON,
            message="Invalid JSON format",
            session_id=session_id,
            details={"json_error": details} if details else None
        )
        
        self.logger.warning(f"JSON error [{error.correlation_id}]: {details}")
        return error
    
    def handle_session_not_found(self, session_id: str) -> ErrorResponse:
        """Handle session not found errors"""
        error = ErrorResponse(
            error_code=ErrorCode.SESSION_NOT_FOUND,
            message=f"Session {session_id} not found",
            session_id=session_id
        )
        
        self.logger.warning(f"Session not found [{error.correlation_id}]: {session_id}")
        return error
    
    def handle_websocket_error(self, 
                              session_id: Optional[str] = None,
                              exception: Optional[Exception] = None) -> ErrorResponse:
        """Handle WebSocket-related errors"""
        error = ErrorResponse(
            error_code=ErrorCode.WEBSOCKET_ERROR,
            message="WebSocket communication error",
            session_id=session_id,
            details={
                "exception_type": type(exception).__name__ if exception else None,
                "exception_message": str(exception) if exception else None
            }
        )
        
        self.logger.error(f"WebSocket error [{error.correlation_id}]: {exception}")
        return error
    
    def handle_internal_error(self, 
                             session_id: Optional[str] = None,
                             exception: Optional[Exception] = None,
                             context: Optional[str] = None) -> ErrorResponse:
        """Handle internal server errors"""
        error = ErrorResponse(
            error_code=ErrorCode.INTERNAL_ERROR,
            message="Internal server error",
            session_id=session_id,
            details={
                "context": context,
                "exception_type": type(exception).__name__ if exception else None
            }
        )
        
        # Log with full traceback for debugging
        if exception:
            self.logger.error(
                f"Internal error [{error.correlation_id}] in {context}: {exception}\n"
                f"Traceback: {traceback.format_exc()}"
            )
        else:
            self.logger.error(f"Internal error [{error.correlation_id}] in {context}")
        
        return error
    
    def handle_rate_limit_error(self, session_id: str) -> ErrorResponse:
        """Handle rate limiting errors"""
        error = ErrorResponse(
            error_code=ErrorCode.RATE_LIMIT_EXCEEDED,
            message="Rate limit exceeded",
            session_id=session_id,
            details={"retry_after": 60}  # Seconds
        )
        
        self.logger.warning(f"Rate limit exceeded [{error.correlation_id}]: {session_id}")
        return error
    
    def handle_unknown_message_type(self, 
                                   message_type: str,
                                   session_id: Optional[str] = None) -> ErrorResponse:
        """Handle unknown message type errors"""
        error = ErrorResponse(
            error_code=ErrorCode.INVALID_MESSAGE_TYPE,
            message=f"Unknown message type: {message_type}",
            session_id=session_id,
            details={
                "received_type": message_type,
                "supported_types": ["ping", "text_message", "audio_data", "status_request"]
            }
        )
        
        self.logger.warning(f"Unknown message type [{error.correlation_id}]: {message_type}")
        return error


class CircuitBreaker:
    """Basic circuit breaker for fault tolerance"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
            else:
                raise Exception("Service unavailable - circuit breaker open")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset"""
        if self.last_failure_time is None:
            return True
        
        return (datetime.now() - self.last_failure_time).seconds > self.recovery_timeout
    
    def _on_success(self):
        """Handle successful call"""
        self.failure_count = 0
        self.state = "CLOSED"
    
    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"


# Global error handler instance
error_handler = ErrorHandler("realtime_voice_ai")
