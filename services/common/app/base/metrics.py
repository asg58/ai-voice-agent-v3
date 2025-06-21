"""
Standardized metrics configuration
"""
import time
from typing import Callable, Dict, Any
from prometheus_client import Counter, Histogram, Gauge, Info

class MetricsManager:
    """Manager for Prometheus metrics"""
    
    def __init__(self, service_name: str):
        """
        Initialize metrics manager
        
        Args:
            service_name: Name of the service
        """
        self.service_name = service_name
        
        # Common metrics
        self.http_requests_total = Counter(
            'http_requests_total',
            'Total number of HTTP requests',
            ['method', 'endpoint', 'status']
        )
        
        self.http_request_duration_seconds = Histogram(
            'http_request_duration_seconds',
            'HTTP request duration in seconds',
            ['method', 'endpoint']
        )
        
        self.active_connections = Gauge(
            'active_connections',
            'Number of active connections'
        )
        
        self.service_info = Info(
            'service_info',
            'Service information'
        )
        self.service_info.info({
            'service_name': service_name,
            'start_time': time.strftime('%Y-%m-%d %H:%M:%S')
        })
    
    def track_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """
        Track HTTP request
        
        Args:
            method: HTTP method
            endpoint: Request endpoint
            status_code: Response status code
            duration: Request duration in seconds
        """
        self.http_requests_total.labels(method=method, endpoint=endpoint, status=status_code).inc()
        self.http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)
    
    def track_connection(self, connected: bool = True):
        """
        Track connection
        
        Args:
            connected: Whether a connection was established (True) or closed (False)
        """
        if connected:
            self.active_connections.inc()
        else:
            self.active_connections.dec()
    
    def _sanitize_path(self, path: str) -> str:
        """
        Sanitize path to prevent cardinality explosion in Prometheus metrics.
        
        Args:
            path: The original path
            
        Returns:
            str: The sanitized path
        """
        import re
        
        # Replace numeric IDs with :id placeholder
        # Example: /users/123 -> /users/:id
        path = re.sub(r'/[0-9]+', '/:id', path)
        
        # Replace UUIDs with :uuid placeholder
        # Example: /users/a1b2c3d4-e5f6-7890-abcd-ef1234567890 -> /users/:uuid
        uuid_pattern = r'/[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}'
        path = re.sub(uuid_pattern, '/:uuid', path, flags=re.IGNORECASE)
        
        # Limit path length to prevent very long paths
        if len(path) > 100:
            path = path[:100] + '...'
        
        return path
    
    def create_middleware(self) -> Callable:
        """
        Create middleware for tracking HTTP requests
        
        Returns:
            Middleware class
        """
        from fastapi import Request
        from starlette.middleware.base import BaseHTTPMiddleware
        
        metrics_manager = self  # Capture self reference for closure
        
        class MetricsMiddleware(BaseHTTPMiddleware):
            async def dispatch(self, request: Request, call_next):
                start_time = time.time()
                
                try:
                    response = await call_next(request)
                    duration = time.time() - start_time
                    
                    # Sanitize path to prevent issues with Prometheus labels
                    path = request.url.path
                    # Normalize paths with IDs to prevent cardinality explosion
                    sanitized_path = metrics_manager._sanitize_path(path)
                    
                    # Use the captured metrics_manager
                    metrics_manager.track_request(
                        method=request.method,
                        endpoint=sanitized_path,
                        status_code=response.status_code,
                        duration=duration
                    )
                    
                    return response
                except Exception as e:
                    duration = time.time() - start_time
                    
                    # Sanitize path to prevent issues with Prometheus labels
                    path = request.url.path
                    # Normalize paths with IDs to prevent cardinality explosion
                    sanitized_path = metrics_manager._sanitize_path(path)
                    
                    # Track failed requests with status code 500
                    metrics_manager.track_request(
                        method=request.method,
                        endpoint=sanitized_path,
                        status_code=500,
                        duration=duration
                    )
                    
                    raise
        
        return MetricsMiddleware