"""
Telemetry API endpoints for Service Mesh
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, Optional, List
from app.models.telemetry import Span, Metric, LogEntry
from app.services.telemetry import TelemetryService
from app.services.circuit_breaker import CircuitBreakerRegistry
from app.services.rate_limiter import RateLimiterRegistry
from loguru import logger

router = APIRouter()


@router.get("/telemetry/spans", response_model=List[Span])
async def get_spans(telemetry_service: TelemetryService = Depends()):
    """
    Get all spans.
    
    Returns:
        List[Span]: List of spans
    """
    return telemetry_service.get_spans()


@router.get("/telemetry/metrics", response_model=List[Metric])
async def get_metrics(telemetry_service: TelemetryService = Depends()):
    """
    Get all metrics.
    
    Returns:
        List[Metric]: List of metrics
    """
    return telemetry_service.get_metrics()


@router.get("/telemetry/logs", response_model=List[LogEntry])
async def get_logs(telemetry_service: TelemetryService = Depends()):
    """
    Get all logs.
    
    Returns:
        List[LogEntry]: List of logs
    """
    return telemetry_service.get_logs()


@router.get("/telemetry/circuit-breakers")
async def get_circuit_breakers(circuit_breaker_registry: CircuitBreakerRegistry = Depends()):
    """
    Get the status of all circuit breakers.
    
    Returns:
        Dict[str, Any]: Status of all circuit breakers
    """
    return circuit_breaker_registry.get_status()


@router.get("/telemetry/rate-limiters")
async def get_rate_limiters(rate_limiter_registry: RateLimiterRegistry = Depends()):
    """
    Get the status of all rate limiters.
    
    Returns:
        Dict[str, Any]: Status of all rate limiters
    """
    return rate_limiter_registry.get_status()