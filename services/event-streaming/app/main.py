"""
Main application module for the Event Streaming service.
"""
import logging
import os
import threading
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from .core.config import settings
from .core.kafka import kafka_client
from .handlers.event_handler import event_handler
from .streams.processors import register_processors
from .api import events, health

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("event-streaming")

# Prometheus metrics endpoint
metrics_app = make_asgi_app()

# Consumer thread
consumer_thread = None
stream_thread = None
should_exit = threading.Event()

def consumer_worker():
    """Worker function for consuming messages."""
    try:
        logger.info("Starting event consumer worker")
        event_handler.start_consuming()
    except Exception as e:
        logger.error(f"Error in consumer worker: {str(e)}")
    finally:
        logger.info("Event consumer worker stopped")

def stream_worker():
    """Worker function for stream processing."""
    try:
        logger.info("Starting stream processing worker")
        event_handler.start_stream_processing()
    except Exception as e:
        logger.error(f"Error in stream worker: {str(e)}")
    finally:
        logger.info("Stream processing worker stopped")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan events for the FastAPI application.
    
    Args:
        app: The FastAPI application
    """
    # Startup: Initialize services
    logger.info("Starting Event Streaming")
    
    # Connect to Kafka
    kafka_client.connect()
    
    # Register stream processors
    register_processors(event_handler)
    
    # Register with service discovery if available
    service_discovery_url = settings.SERVICE_DISCOVERY_URL
    if service_discovery_url:
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{service_discovery_url}/services",
                    json={
                        "id": "event-streaming",
                        "name": "Event Streaming",
                        "host": os.environ.get("HOST", "event-streaming"),
                        "port": int(os.environ.get("PORT", 8000)),
                        "health_check": "/health/health"
                    }
                )
                if response.status_code == 201:
                    logger.info("Registered with service discovery")
                else:
                    logger.warning(f"Failed to register with service discovery: {response.status_code}")
        except Exception as e:
            logger.error(f"Error registering with service discovery: {str(e)}")
    
    # Start consumer thread
    global consumer_thread
    consumer_thread = threading.Thread(target=consumer_worker)
    consumer_thread.daemon = True
    consumer_thread.start()
    
    # Start stream processing thread if enabled
    if settings.STREAM_PROCESSING_ENABLED:
        global stream_thread
        stream_thread = threading.Thread(target=stream_worker)
        stream_thread.daemon = True
        stream_thread.start()
    
    yield
    
    # Shutdown: Cleanup resources
    logger.info("Shutting down Event Streaming")
    
    # Stop consumer and stream processing
    event_handler.stop_consuming()
    
    # Wait for threads to exit
    if consumer_thread:
        consumer_thread.join(timeout=5)
    
    if stream_thread:
        stream_thread.join(timeout=5)
    
    # Close Kafka connection
    kafka_client.close()
    
    # Deregister from service discovery if available
    if service_discovery_url:
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.delete(f"{service_discovery_url}/services/event-streaming")
                if response.status_code == 204:
                    logger.info("Deregistered from service discovery")
                else:
                    logger.warning(f"Failed to deregister from service discovery: {response.status_code}")
        except Exception as e:
            logger.error(f"Error deregistering from service discovery: {str(e)}")

# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Event Streaming for the AI Voice Agent Platform",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Mount Prometheus metrics endpoint
app.mount("/metrics", metrics_app)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# Include routers
app.include_router(events.router, prefix=settings.API_V1_STR)
app.include_router(health.router)

# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint for the Event Streaming service.
    
    Returns:
        dict: A welcome message
    """
    return {
        "message": "Welcome to the AI Voice Agent Event Streaming",
        "docs": "/docs",
        "health": "/health"
    }