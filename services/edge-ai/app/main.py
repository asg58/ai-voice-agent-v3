"""
Main application module for Edge AI Service
"""
import threading
import time
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from loguru import logger

from app.api import health, process
from app.core.config import settings
from app.services.service_registry import ServiceRegistry

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="Edge AI Service for processing AI models on edge devices",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api/v1")
app.include_router(process.router, prefix="/api/v1")

# Service registry instance
service_registry = ServiceRegistry()

# Heartbeat thread
heartbeat_thread = None
heartbeat_running = False


def send_heartbeats():
    """Send heartbeats to service discovery."""
    global heartbeat_running
    while heartbeat_running:
        try:
            service_registry.send_heartbeat()
        except Exception as e:
            logger.error(f"Error in heartbeat thread: {str(e)}")
        time.sleep(30)  # Send heartbeat every 30 seconds


# Custom OpenAPI schema
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=f"{settings.APP_NAME} API",
        version=settings.APP_VERSION,
        description="API for Edge AI Service",
        routes=app.routes,
    )
    
    # Add custom schema components here if needed
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


@app.on_event("startup")
async def startup_event():
    """
    Startup event handler.
    """
    global heartbeat_thread, heartbeat_running
    
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    
    # Register with service discovery if enabled
    if os.getenv("SERVICE_DISCOVERY_HOST"):
        try:
            if service_registry.register():
                # Start heartbeat thread
                heartbeat_running = True
                heartbeat_thread = threading.Thread(target=send_heartbeats)
                heartbeat_thread.daemon = True
                heartbeat_thread.start()
                logger.info("Service registered with Service Discovery")
            else:
                logger.warning("Failed to register with Service Discovery")
        except Exception as e:
            logger.error(f"Error registering with Service Discovery: {str(e)}")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Shutdown event handler.
    """
    global heartbeat_running
    
    logger.info(f"Shutting down {settings.APP_NAME}")
    
    # Deregister from service discovery
    if os.getenv("SERVICE_DISCOVERY_HOST"):
        try:
            # Stop heartbeat thread
            heartbeat_running = False
            if heartbeat_thread:
                heartbeat_thread.join(timeout=1)
            
            # Deregister service
            if service_registry.deregister():
                logger.info("Service deregistered from Service Discovery")
            else:
                logger.warning("Failed to deregister from Service Discovery")
        except Exception as e:
            logger.error(f"Error deregistering from Service Discovery: {str(e)}")


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint.
    
    Returns:
        dict: Basic service information
    """
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }