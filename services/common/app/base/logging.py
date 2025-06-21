"""
Standardized logging configuration
"""
import logging
import logging.config
import sys
from typing import Optional, Dict, Any

def configure_logging(
    service_name: str,
    log_level: str = "INFO",
    log_format: Optional[str] = None,
    json_logs: bool = False,
    log_config: Optional[Dict[str, Any]] = None,
):
    """
    Configure logging for a service
    
    Args:
        service_name: Name of the service
        log_level: Logging level
        log_format: Log format string
        json_logs: Whether to output logs in JSON format
        log_config: Custom logging configuration
    """
    if log_config:
        logging.config.dictConfig(log_config)
        return
    
    # Default format
    if not log_format:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        stream=sys.stdout,
    )
    
    # Create service logger
    logger = logging.getLogger(service_name)
    
    # Suppress overly verbose loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    
    return logger