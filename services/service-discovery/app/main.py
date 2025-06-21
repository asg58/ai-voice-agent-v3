"""
Main application module for Service Discovery Service
"""
import logging
import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from services.common.app.base.app_factory import create_app
from services.common.app.base.logging import configure_logging
from app.core.config import settings
from app.api import health, services

# Configure logging
logger = configure_logging(
    service_name="service-discovery",
    log_level=settings.LOG_LEVEL
)

# Background task for health checking
health_check_task = None

# Lifespan handler
async def lifespan_handler(app: FastAPI, event: str) -> None:
    """
    Handle application lifecycle events
    
    Args:
        app: FastAPI application
        event: Lifecycle event ("startup" or "shutdown")
    """
    global health_check_task
    
    if event == "startup":
        logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
        
        # Start health check worker
        from app.api.services import health_check_worker
        health_check_task = asyncio.create_task(health_check_worker())
        
        logger.info(f"{settings.APP_NAME} is ready!")
    else:  # shutdown
        logger.info(f"Shutting down {settings.APP_NAME}...")
        
        # Cancel health check worker
        if health_check_task:
            health_check_task.cancel()
            try:
                await health_check_task
            except asyncio.CancelledError:
                pass

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
app.include_router(services.router, prefix="/services", tags=["Services"])

# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint for the Service Discovery service
    
    Returns:
        dict: A welcome message
    """
    return {
        "message": "Welcome to the AI Voice Agent Service Discovery",
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