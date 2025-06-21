"""
Metrics Middleware for Voice Module

Prometheus metrics collection for the Voice Module service.
"""

import time
from typing import Callable
from fastapi import FastAPI, Request, Response
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
import logging

logger = logging.getLogger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter(
    'voice_module_requests_total',
    'Total requests processed by Voice Module',
    ['method', 'endpoint', 'status_code']
)

REQUEST_DURATION = Histogram(
    'voice_module_request_duration_seconds',
    'Request duration in seconds',
    ['method', 'endpoint']
)

ACTIVE_WEBSOCKET_CONNECTIONS = Gauge(
    'voice_module_websocket_connections',
    'Number of active WebSocket connections'
)

VOICE_PROCESSING_DURATION = Histogram(
    'voice_module_processing_seconds',
    'Voice processing duration in seconds',
    ['operation_type']
)

TRANSCRIPTION_COUNT = Counter(
    'voice_module_transcriptions_total',
    'Total transcription requests',
    ['status', 'language']
)

SYNTHESIS_COUNT = Counter(
    'voice_module_synthesis_total',
    'Total speech synthesis requests',
    ['status', 'voice']
)

AUDIO_FILE_SIZE = Histogram(
    'voice_module_audio_file_size_bytes',
    'Size of processed audio files in bytes'
)

VAD_DETECTIONS = Counter(
    'voice_module_vad_detections_total',
    'Voice activity detection results',
    ['has_voice']
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
    
    logger.info("Prometheus metrics enabled for Voice Module")


def record_voice_processing_time(operation_type: str, duration: float) -> None:
    """Record voice processing time metric."""
    VOICE_PROCESSING_DURATION.labels(operation_type=operation_type).observe(duration)


def record_transcription(status: str, language: str = "unknown") -> None:
    """Record transcription request metric."""
    TRANSCRIPTION_COUNT.labels(status=status, language=language).inc()


def record_synthesis(status: str, voice: str = "unknown") -> None:
    """Record speech synthesis request metric."""
    SYNTHESIS_COUNT.labels(status=status, voice=voice).inc()


def record_audio_file_size(size_bytes: int) -> None:
    """Record audio file size metric."""
    AUDIO_FILE_SIZE.observe(size_bytes)


def record_vad_detection(has_voice: bool) -> None:
    """Record voice activity detection result."""
    VAD_DETECTIONS.labels(has_voice=str(has_voice).lower()).inc()


def update_websocket_connections(count: int) -> None:
    """Update active WebSocket connections gauge."""
    ACTIVE_WEBSOCKET_CONNECTIONS.set(count)