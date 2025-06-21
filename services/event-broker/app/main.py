"""
Main application module for Event Broker Service
"""
import logging
import os
import threading
import time
import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from common.app.base.app_factory import create_app
from common.app.base.logging import configure_logging
from app.core.config import settings
from app.core.rabbitmq import rabbitmq_client
from app.handlers.event_handler import event_handler
from app.api import events, health

# Configure logging
logger = configure_logging(
    service_name="event-broker",
    log_level=settings.LOG_LEVEL
)

# Consumer thread
consumer_thread = None
should_exit = threading.Event()

def consumer_worker():
    """Worker function for consuming messages"""
    try:
        logger.info("Starting event consumer worker")
        event_handler.start_consuming()
    except Exception as e:
        logger.error(f"Error in consumer worker: {str(e)}")
    finally:
        logger.info("Event consumer worker stopped")

# Lifespan handler
async def lifespan_handler(app: FastAPI, event: str) -> None:
    """
    Handle application lifecycle events
    
    Args:
        app: FastAPI application
        event: Lifecycle event ("startup" or "shutdown")
    """
    global consumer_thread
    
    if event == "startup":
        logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
        
        # Connect to RabbitMQ
        rabbitmq_client.connect()
        
        # Register with service discovery if available
        await register_with_service_discovery()
        
        # Start consumer thread
        consumer_thread = threading.Thread(target=consumer_worker)
        consumer_thread.daemon = True
        consumer_thread.start()
        
        logger.info(f"{settings.APP_NAME} is ready!")
    else:  # shutdown
        logger.info(f"Shutting down {settings.APP_NAME}...")
        
        # Stop consumer
        event_handler.stop_consuming()
        
        # Wait for consumer thread to exit
        if consumer_thread:
            consumer_thread.join(timeout=5)
        
        # Close RabbitMQ connection
        rabbitmq_client.close()
        
        # Deregister from service discovery
        await deregister_from_service_discovery()

async def register_with_service_discovery():
    """Register service with service discovery"""
    service_discovery_url = settings.SERVICE_DISCOVERY_URL
    if service_discovery_url:
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{service_discovery_url}/services",
                    json={
                        "id": "event-broker",
                        "name": settings.APP_NAME,
                        "host": os.environ.get("HOST", "event-broker"),
                        "port": int(os.environ.get("PORT", settings.PORT)),
                        "health_check": "/health/health"
                    }
                )
                if response.status_code == 201:
                    logger.info("Registered with service discovery")
                else:
                    logger.warning(f"Failed to register with service discovery: {response.status_code}")
        except Exception as e:
            logger.error(f"Error registering with service discovery: {str(e)}")

async def deregister_from_service_discovery():
    """Deregister service from service discovery"""
    service_discovery_url = settings.SERVICE_DISCOVERY_URL
    if service_discovery_url:
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.delete(f"{service_discovery_url}/services/event-broker")
                if response.status_code == 204:
                    logger.info("Deregistered from service discovery")
                else:
                    logger.warning(f"Failed to deregister from service discovery: {response.status_code}")
        except Exception as e:
            logger.error(f"Error deregistering from service discovery: {str(e)}")

# Create FastAPI application
app = create_app(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    lifespan_handler=lifespan_handler,
    cors_origins=settings.CORS_ORIGINS,
    enable_metrics=settings.ENABLE_METRICS
)

# Include routers
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(events.router, prefix="/api/v1", tags=["Events"])

# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint for the Event Broker service
    
    Returns:
        dict: A welcome message
    """
    return {
        "message": "Welcome to the AI Voice Agent Event Broker",
        "docs": "/docs",
        "health": "/health"
    }

# For direct execution
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )