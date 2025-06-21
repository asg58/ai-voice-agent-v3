"""
Proxy service for Service Mesh
"""
import requests
import time
from typing import Dict, Any, Optional, List, Tuple
from loguru import logger
from app.models.mesh import ProxyRequest, ProxyResponse, ServiceInstance
from app.services.circuit_breaker import CircuitBreakerRegistry
from app.services.rate_limiter import RateLimiterRegistry
from app.services.router import Router

class ProxyService:
    """
    Proxy service implementation.

    This class provides methods for proxying requests to services.
    """

    def __init__(
        self,
        router: Any,
        circuit_breaker_registry: Any,
        rate_limiter_registry: Any
    ):
        """
        Initialize the proxy service.

        Args:
            router: Router
            circuit_breaker_registry: Circuit breaker registry
            rate_limiter_registry: Rate limiter registry
        """
        self.router = router
        self.circuit_breaker_registry = circuit_breaker_registry
        self.rate_limiter_registry = rate_limiter_registry

        logger.info("Proxy service initialized")

    async def proxy_request(self, request: ProxyRequest) -> ProxyResponse:
        """
        Proxy a request to a service.

        Args:
            request: Proxy request

        Returns:
            ProxyResponse: Proxy response
        """
        # Route the request
        service_instance = await self.router.route_request(
            request.path,
            request.method,
            request.headers
        )

        if not service_instance:
            logger.warning(f"No service found for {request.method} {request.path}")  
            return ProxyResponse(
                status_code=404,
                headers={},
                body={"error": "Service not found"}
            )

        # Check circuit breaker
        # Get service-specific circuit breaker settings from router
        route = await self.router.match_route(request.path, request.method, request.headers)
        service_name = service_instance.name
        
        # Default circuit breaker settings
        threshold = 5
        timeout = 30
        
        # Get service-specific settings if available
        if route and hasattr(route, 'service') and hasattr(route.service, 'circuit_breaker'):
            threshold = route.service.circuit_breaker.threshold
            timeout = route.service.circuit_breaker.timeout
        
        circuit_breaker = self.circuit_breaker_registry.get_circuit_breaker(
            service_name,
            threshold=threshold,
            timeout=timeout
        )

        if not circuit_breaker.allow_request():
            logger.warning(f"Circuit breaker open for {service_instance.name}")      
            return ProxyResponse(
                status_code=503,
                headers={},
                body={"error": "Service unavailable"}
            )

        # Check rate limiter
        # Default rate limiter settings
        requests = 100
        window = 60
        
        # Get service-specific settings if available
        if route and hasattr(route, 'service') and hasattr(route.service, 'rate_limit'):
            requests = route.service.rate_limit.requests
            window = route.service.rate_limit.window
            
        rate_limiter = self.rate_limiter_registry.get_rate_limiter(
            service_name,
            requests=requests,
            window=window
        )

        if not rate_limiter.allow_request():
            logger.warning(f"Rate limit exceeded for {service_instance.name}")       
            return ProxyResponse(
                status_code=429,
                headers={
                    "X-RateLimit-Limit": str(rate_limiter.requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(rate_limiter.get_reset_time()))     
                },
                body={"error": "Rate limit exceeded"}
            )

        # Proxy the request
        try:
            # Build the URL
            url = f"http://{service_instance.host}:{service_instance.port}{request.path}"
            if request.query_params:
                query_string = "&".join([f"{k}={v}" for k, v in request.query_params.items()])
                url = f"{url}?{query_string}"

            # Send the request
            start_time = time.time()
            response = requests.request(
                method=request.method,
                url=url,
                headers=request.headers,
                json=request.body,
                timeout=10
            )
            end_time = time.time()

            # Record success
            circuit_breaker.record_success()

            # Log the request
            logger.info(f"Proxied {request.method} {request.path} to {service_instance.name} ({service_instance.host}:{service_instance.port}) - {response.status_code} in {(end_time - start_time) * 1000:.2f}ms")

            # Return the response
            body = None
            if response.content:
                try:
                    # Try to parse as JSON
                    body = response.json()
                except ValueError:
                    # If not JSON, return as text
                    body = {"text": response.text}
            
            return ProxyResponse(
                status_code=response.status_code,
                headers=dict(response.headers),
                body=body
            )
        except Exception as e:
            # Record failure
            circuit_breaker.record_failure()

            logger.error(f"Error proxying request to {service_instance.name}: {str(e)}")
            return ProxyResponse(
                status_code=500,
                headers={},
                body={"error": "Internal server error"}
            )