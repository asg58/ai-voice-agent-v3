"""
Metrics Middleware

Prometheus metrics collection for the Core Engine service.
"""

import time
from typing import Callable
from fastapi import FastAPI, Request, Response
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
import logging

logger = logging.getLogger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter(
    'core_engine_requests_total',
    'Total requests processed by Core Engine',
    ['method', 'endpoint', 'status_code']
)

REQUEST_DURATION = Histogram(
    'core_engine_request_duration_seconds',
    'Request duration in seconds',
    ['method', 'endpoint']
)

ACTIVE_CONVERSATIONS = Gauge(
    'core_engine_active_conversations',
    'Number of active conversations'
)

AI_PROCESSING_DURATION = Histogram(
    'core_engine_ai_processing_seconds',
    'AI processing duration in seconds',
    ['request_type']
)

OPENAI_API_CALLS = Counter(
    'core_engine_openai_calls_total',
    'Total OpenAI API calls',
    ['model', 'status']
)


def add_prometheus_metrics(app: FastAPI) -> None:
    """Add Prometheus metrics collection to the FastAPI app."""
    
    @app.middleware("http")
    async def metrics_middleware(request: Request, call_next: Callable) -> Response:
        """Middleware to collect request metrics."""
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Record metrics
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status_code=response.status_code
        ).inc()
        
        REQUEST_DURATION.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)
        
        return response
    
    @app.get("/metrics")
    async def get_metrics():
        """Endpoint to expose Prometheus metrics."""
        return Response(
            generate_latest(),
            media_type=CONTENT_TYPE_LATEST
        )
    
    logger.info("Prometheus metrics enabled")


def record_ai_processing_time(request_type: str, duration: float) -> None:
    """Record AI processing time metric."""
    AI_PROCESSING_DURATION.labels(request_type=request_type).observe(duration)


def record_openai_call(model: str, status: str) -> None:
    """Record OpenAI API call metric."""
    OPENAI_API_CALLS.labels(model=model, status=status).inc()


def update_active_conversations(count: int) -> None:
    """Update active conversations gauge."""
    ACTIVE_CONVERSATIONS.set(count)