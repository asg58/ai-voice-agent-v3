"""
Common middleware for FastAPI applications
"""
import time
import logging
from typing import Callable, Dict, Any, List
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging requests and responses"""
    
    def __init__(self, app: FastAPI, service_name: str = "service"):
        """
        Initialize logging middleware
        
        Args:
            app: FastAPI application
            service_name: Name of the service
        """
        super().__init__(app)
        self.service_name = service_name
    
    async def dispatch(self, request: Request, call_next):
        """
        Process request and log details
        
        Args:
            request: HTTP request
            call_next: Next middleware or endpoint handler
            
        Returns:
            HTTP response
        """
        start_time = time.time()
        
        # Log request
        logger.info(f"Request: {request.method} {request.url.path}")
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Log response
            logger.info(
                f"Response: {request.method} {request.url.path} - "
                f"Status: {response.status_code} - "
                f"Duration: {duration:.3f}s"
            )
            
            return response
        
        except Exception as e:
            # Log exception
            logger.error(
                f"Error processing request: {request.method} {request.url.path} - "
                f"Error: {str(e)}"
            )
            raise

def create_middleware_list(
    service_name: str,
    enable_logging: bool = True,
    enable_metrics: bool = True,
    custom_middleware: List[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Create a list of middleware configurations
    
    Args:
        service_name: Name of the service
        enable_logging: Whether to enable logging middleware
        enable_metrics: Whether to enable metrics middleware
        custom_middleware: List of custom middleware configurations
        
    Returns:
        List of middleware configurations
    """
    middleware_list = []
    
    # Add logging middleware
    if enable_logging:
        middleware_list.append({
            "class": LoggingMiddleware,
            "service_name": service_name
        })
    
    # Add metrics middleware
    if enable_metrics:
        from .metrics import MetricsManager
        metrics_manager = MetricsManager(service_name)
        MetricsMiddleware = metrics_manager.create_middleware()
        middleware_list.append({
            "class": MetricsMiddleware,
        })
    
    # Add custom middleware
    if custom_middleware:
        middleware_list.extend(custom_middleware)
    
    return middleware_list