"""
Centralized Logging Configuration

This module provides standardized logging configuration for all services
in the AI Voice Agent platform.
"""

import logging
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional
from logging.handlers import RotatingFileHandler
import structlog


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add extra fields if present
        if hasattr(record, 'service_name'):
            log_entry['service_name'] = record.service_name
        
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
            
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry, ensure_ascii=False)


def setup_logging(
    service_name: str,
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    enable_json: bool = True
) -> logging.Logger:
    """
    Setup standardized logging configuration for a service.
    
    Args:
        service_name: Name of the service
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        max_file_size: Maximum log file size before rotation
        backup_count: Number of backup files to keep
        enable_json: Whether to use JSON formatting
        
    Returns:
        Configured logger instance
    """
    # Clear existing handlers
    logging.getLogger().handlers.clear()
    
    # Create logger
    logger = logging.getLogger(service_name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Create formatters
    if enable_json:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_file_size,
            backupCount=backup_count
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Add service name to all log records
    class ServiceFilter(logging.Filter):
        def filter(self, record):
            record.service_name = service_name
            return True
    
    for handler in logger.handlers:
        handler.addFilter(ServiceFilter())
    
    logger.info(f"Logging initialized for service: {service_name}")
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the specified name."""
    return logging.getLogger(name)


class LoggerAdapter:
    """Logger adapter for adding context to log messages."""
    
    def __init__(self, logger: logging.Logger, extra: Dict[str, Any]):
        self.logger = logger
        self.extra = extra
    
    def _log(self, level: int, message: str, *args, **kwargs):
        """Log with extra context."""
        if self.logger.isEnabledFor(level):
            # Add extra context to log record
            extra = kwargs.pop('extra', {})
            extra.update(self.extra)
            kwargs['extra'] = extra
            self.logger.log(level, message, *args, **kwargs)
    
    def debug(self, message: str, *args, **kwargs):
        self._log(logging.DEBUG, message, *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs):
        self._log(logging.INFO, message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        self._log(logging.WARNING, message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs):
        self._log(logging.ERROR, message, *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs):
        self._log(logging.CRITICAL, message, *args, **kwargs)


def get_context_logger(
    name: str,
    request_id: Optional[str] = None,
    user_id: Optional[str] = None,
    **extra_context
) -> LoggerAdapter:
    """
    Get a logger with additional context.
    
    Args:
        name: Logger name
        request_id: Optional request ID
        user_id: Optional user ID
        **extra_context: Additional context fields
        
    Returns:
        Logger adapter with context
    """
    logger = get_logger(name)
    context = {}
    
    if request_id:
        context['request_id'] = request_id
    
    if user_id:
        context['user_id'] = user_id
    
    context.update(extra_context)
    
    return LoggerAdapter(logger, context)


# Structured logging setup using structlog
def setup_structlog(service_name: str) -> None:
    """
    Setup structured logging using structlog.
    
    Args:
        service_name: Name of the service
    """
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="ISO"),
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=False,
    )
    
    # Add service name to context
    structlog.contextvars.bind_contextvars(service_name=service_name)


# Export main functions
__all__ = [
    'setup_logging',
    'get_logger',
    'get_context_logger',
    'setup_structlog',
    'JSONFormatter',
    'LoggerAdapter'
]"""
Centralized Logging Configuration

This module provides standardized logging configuration for all services
in the AI Voice Agent platform.
"""

import logging
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional
from logging.handlers import RotatingFileHandler
import structlog


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add extra fields if present
        if hasattr(record, 'service_name'):
            log_entry['service_name'] = record.service_name
        
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
            
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry, ensure_ascii=False)


def setup_logging(
    service_name: str,
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    enable_json: bool = True
) -> logging.Logger:
    """
    Setup standardized logging configuration for a service.
    
    Args:
        service_name: Name of the service
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        max_file_size: Maximum log file size before rotation
        backup_count: Number of backup files to keep
        enable_json: Whether to use JSON formatting
        
    Returns:
        Configured logger instance
    """
    # Clear existing handlers
    logging.getLogger().handlers.clear()
    
    # Create logger
    logger = logging.getLogger(service_name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Create formatters
    if enable_json:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_file_size,
            backupCount=backup_count
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Add service name to all log records
    class ServiceFilter(logging.Filter):
        def filter(self, record):
            record.service_name = service_name
            return True
    
    for handler in logger.handlers:
        handler.addFilter(ServiceFilter())
    
    logger.info(f"Logging initialized for service: {service_name}")
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the specified name."""
    return logging.getLogger(name)


class LoggerAdapter:
    """Logger adapter for adding context to log messages."""
    
    def __init__(self, logger: logging.Logger, extra: Dict[str, Any]):
        self.logger = logger
        self.extra = extra
    
    def _log(self, level: int, message: str, *args, **kwargs):
        """Log with extra context."""
        if self.logger.isEnabledFor(level):
            # Add extra context to log record
            extra = kwargs.pop('extra', {})
            extra.update(self.extra)
            kwargs['extra'] = extra
            self.logger.log(level, message, *args, **kwargs)
    
    def debug(self, message: str, *args, **kwargs):
        self._log(logging.DEBUG, message, *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs):
        self._log(logging.INFO, message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        self._log(logging.WARNING, message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs):
        self._log(logging.ERROR, message, *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs):
        self._log(logging.CRITICAL, message, *args, **kwargs)


def get_context_logger(
    name: str,
    request_id: Optional[str] = None,
    user_id: Optional[str] = None,
    **extra_context
) -> LoggerAdapter:
    """
    Get a logger with additional context.
    
    Args:
        name: Logger name
        request_id: Optional request ID
        user_id: Optional user ID
        **extra_context: Additional context fields
        
    Returns:
        Logger adapter with context
    """
    logger = get_logger(name)
    context = {}
    
    if request_id:
        context['request_id'] = request_id
    
    if user_id:
        context['user_id'] = user_id
    
    context.update(extra_context)
    
    return LoggerAdapter(logger, context)


# Structured logging setup using structlog
def setup_structlog(service_name: str) -> None:
    """
    Setup structured logging using structlog.
    
    Args:
        service_name: Name of the service
    """
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="ISO"),
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=False,
    )
    
    # Add service name to context
    structlog.contextvars.bind_contextvars(service_name=service_name)


# Export main functions
__all__ = [
    'setup_logging',
    'get_logger',
    'get_context_logger',
    'setup_structlog',
    'JSONFormatter',
    'LoggerAdapter'
]