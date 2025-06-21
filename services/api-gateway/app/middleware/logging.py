"""
Logging middleware for the API Gateway.
"""
import time
import uuid
import logging
from typing import Callable
from fastapi import Request, Response
from common.app.base.metrics import MetricsManager
from ..core.config import settings

# Configure logging
logger = logging.getLogger(f"{settings.APP_NAME}.middleware.logging")

# Initialize metrics manager
metrics = MetricsManager(service_name=settings.APP_NAME)

async def logging_middleware(request: Request, call_next: Callable) -> Response:
    """
    Middleware to log requests and responses.
    
    Args:
        request: The incoming request
        call_next: The next middleware or route handler
        
    Returns:
        Response: The response from the next handler
    """
    # Generate a unique request ID
    request_id = str(uuid.uuid4())
    
    # Add request ID to request state
    request.state.request_id = request_id
    
    # Get client IP
    client_ip = request.client.host if request.client else "unknown"
    
    # Get path and sanitize it for logging (prevent log injection)
    path = request.url.path
    sanitized_path = path.replace('\n', '').replace('\r', '')
    
    # Log the request (with limited query params to prevent sensitive data exposure)
    query_params = str(request.query_params)
    if len(query_params) > 100:
        query_params = query_params[:100] + "..."
        
    logger.info(
        f"Request {request_id}: {request.method} {sanitized_path} "
        f"from {client_ip} - Query: {query_params}"
    )
    
    # Record start time
    start_time = time.time()
    
    # Process the request
    try:
        response = await call_next(request)
        
        # Calculate request duration
        duration = time.time() - start_time
        
        # Update Prometheus metrics
        # We'll track metrics here regardless of ENABLE_METRICS setting
        # to ensure metrics are always captured
        metrics.track_request(
            method=request.method,
            endpoint=sanitized_path,
            status_code=response.status_code,
            duration=duration
        )
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        # Log the response
        logger.info(
            f"Response {request_id}: {response.status_code} - "
            f"Duration: {duration:.4f}s"
        )
        
        return response
    except Exception as e:
        # Calculate duration
        duration = time.time() - start_time
        
        # Log the exception
        logger.error(
            f"Error {request_id}: {str(e)} - "
            f"Duration: {duration:.4f}s"
        )
        
        # Update metrics for failed requests
        # We'll track metrics here regardless of ENABLE_METRICS setting
        metrics.track_request(
            method=request.method,
            endpoint=sanitized_path,
            status_code=500,  # Assume 500 for exceptions
            duration=duration
        )
        
        # Re-raise the exception
        raise