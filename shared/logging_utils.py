"""
Shared logging utilities for the AI Voice Agent services.

This module provides standardized logging configuration and utilities
to ensure consistent logging across all services and scripts.
"""
import logging
import sys
from typing import Optional
from pathlib import Path


class VoiceAgentLogger:
    """
    Production-ready logger with proper formatting and configuration.
    
    Features:
    - Consistent formatting across all services
    - Proper log levels with colored output
    - File and console output support
    - Structured logging capabilities
    """
    
    def __init__(
        self,
        name: str,
        level: str = "INFO",
        log_file: Optional[Path] = None,
        format_string: Optional[str] = None
    ):
        """
        Initialize logger with standardized configuration.
        
        Args:
            name: Logger name (usually __name__)
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Optional file path for logging to file
            format_string: Custom format string (uses default if None)
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        
        # Prevent duplicate handlers
        if self.logger.handlers:
            return
            
        # Default format with timestamp, name, level, and message
        if format_string is None:
            format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        formatter = logging.Formatter(format_string)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # File handler (optional)
        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def info(self, message: str) -> None:
        """Log info message."""
        self.logger.info(message)
    
    def error(self, message: str, exc_info: bool = False) -> None:
        """Log error message with optional exception info."""
        self.logger.error(message, exc_info=exc_info)
    
    def warning(self, message: str) -> None:
        """Log warning message."""
        self.logger.warning(message)
    
    def debug(self, message: str) -> None:
        """Log debug message."""
        self.logger.debug(message)
    
    def critical(self, message: str) -> None:
        """Log critical message."""
        self.logger.critical(message)


def setup_service_logging(
    service_name: str,
    level: str = "INFO",
    log_dir: Optional[Path] = None
) -> logging.Logger:
    """
    Set up standardized logging for a service.
    
    Args:
        service_name: Name of the service
        level: Log level
        log_dir: Directory for log files
        
    Returns:
        Configured logger instance
    """
    log_file = None
    if log_dir:
        log_file = log_dir / f"{service_name}.log"
    
    voice_logger = VoiceAgentLogger(
        name=service_name,
        level=level,
        log_file=log_file
    )
    
    return voice_logger.logger


def setup_script_logging(script_name: str, level: str = "INFO") -> logging.Logger:
    """
    Set up standardized logging for scripts.
    
    Args:
        script_name: Name of the script
        level: Log level
        
    Returns:
        Configured logger instance
    """
    voice_logger = VoiceAgentLogger(
        name=script_name,
        level=level
    )
    
    return voice_logger.logger


# Pre-configured logger instances for common use cases
def get_logger(name: str, level: str = "INFO") -> logging.Logger:
    """
    Get a standardized logger instance.
    
    Args:
        name: Logger name (usually __name__)
        level: Log level
        
    Returns:
        Configured logger instance
    """
    voice_logger = VoiceAgentLogger(name=name, level=level)
    return voice_logger.logger


# Export commonly used functions
__all__ = [
    'VoiceAgentLogger',
    'setup_service_logging', 
    'setup_script_logging',
    'get_logger'
]
