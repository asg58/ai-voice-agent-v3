"""
Mesh models for Service Mesh
"""
from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, ForwardRef
from enum import Enum


class ServiceStatus(str, Enum):
    """Service status enum"""
    HEALTHY = "healthy"
    WARNING = "warning"
    ERROR = "error"
    UNKNOWN = "unknown"


class ServiceProtocol(str, Enum):
    """Service protocol enum"""
    HTTP = "http"
    HTTPS = "https"
    GRPC = "grpc"
    TCP = "tcp"
    UDP = "udp"


class ServiceInstance(BaseModel):
    """
    Service instance model.
    
    Attributes:
        id: Service instance ID
        name: Service name
        host: Service host
        port: Service port
        status: Service status
        protocol: Service protocol
        metadata: Service metadata
    """
    id: str
    name: str
    host: str
    port: int
    status: ServiceStatus = ServiceStatus.UNKNOWN
    protocol: ServiceProtocol = ServiceProtocol.HTTP
    metadata: Dict[str, Any] = {}


class RouteDestination(BaseModel):
    """
    Route destination model.
    
    Attributes:
        service_name: Service name
        weight: Routing weight
    """
    service_name: str
    weight: int = 100


class RouteMatch(BaseModel):
    """
    Route match model.
    
    Attributes:
        path: Path to match
        method: HTTP method to match
        headers: Headers to match
    """
    path: Optional[str] = None
    method: Optional[str] = None
    headers: Dict[str, str] = {}


class Route(BaseModel):
    """
    Route model.
    
    Attributes:
        name: Route name
        match: Route match criteria
        destinations: Route destinations
        service: Optional reference to the parent service
    """
    name: str
    match: RouteMatch
    destinations: List[RouteDestination]
    service: Optional['ServiceConfig'] = None


class CircuitBreakerSettings(BaseModel):
    """
    Circuit breaker settings model.
    
    Attributes:
        enabled: Whether circuit breaking is enabled
        threshold: Number of consecutive failures before opening the circuit
        timeout: Time in seconds before trying to close the circuit
    """
    enabled: bool = True
    threshold: int = 5
    timeout: int = 30


class RateLimitSettings(BaseModel):
    """
    Rate limit settings model.
    
    Attributes:
        enabled: Whether rate limiting is enabled
        requests: Number of requests allowed
        window: Time window in seconds
    """
    enabled: bool = True
    requests: int = 100
    window: int = 60


class ServiceConfig(BaseModel):
    """
    Service configuration model.
    
    Attributes:
        name: Service name
        circuit_breaker: Circuit breaker settings
        rate_limit: Rate limit settings
        routes: Service routes
    """
    name: str
    circuit_breaker: CircuitBreakerSettings = CircuitBreakerSettings()
    rate_limit: RateLimitSettings = RateLimitSettings()
    routes: List[Route] = []


class MeshConfig(BaseModel):
    """
    Mesh configuration model.
    
    Attributes:
        services: Service configurations
    """
    services: List[ServiceConfig] = []


class ProxyRequest(BaseModel):
    """
    Proxy request model.
    
    Attributes:
        service_name: Target service name
        path: Request path
        method: HTTP method
        headers: Request headers
        query_params: Query parameters
        body: Request body
    """
    service_name: str
    path: str
    method: str
    headers: Dict[str, str] = {}
    query_params: Dict[str, str] = {}
    body: Optional[Any] = None


class ProxyResponse(BaseModel):
    """
    Proxy response model.
    
    Attributes:
        status_code: Response status code
        headers: Response headers
        body: Response body
    """
    status_code: int
    headers: Dict[str, str] = {}
    body: Any


from pydantic import BaseModel
from typing import Dict, Any

class ServiceInstanceModel(BaseModel):
    id: str
    name: str
    host: str
    port: int
    status: str
    protocol: str
    metadata: Dict[str, Any]