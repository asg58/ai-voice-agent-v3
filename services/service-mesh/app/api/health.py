"""
Health API endpoints for Service Mesh
"""
from fastapi import APIRouter, Depends
from app.core.config import settings
from app.services.circuit_breaker import CircuitBreakerRegistry
from app.services.rate_limiter import RateLimiterRegistry
from loguru import logger

router = APIRouter()


@router.get("/health")
async def health_check(
    circuit_breaker_registry: CircuitBreakerRegistry = Depends(),
    rate_limiter_registry: RateLimiterRegistry = Depends()
):
    """
    Health check endpoint.
    
    Returns:
        dict: Health status
    """
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "features": {
            "tracing_enabled": settings.TRACING_ENABLED,
            "metrics_enabled": settings.METRICS_ENABLED,
            "circuit_breaker_enabled": settings.CIRCUIT_BREAKER_ENABLED,
            "rate_limit_enabled": settings.RATE_LIMIT_ENABLED,
            "mtls_enabled": settings.MTLS_ENABLED
        },
        "circuit_breakers": len(circuit_breaker_registry.circuit_breakers),
        "rate_limiters": len(rate_limiter_registry.rate_limiters)
    }