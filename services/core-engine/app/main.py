"""
Core Engine Service - Main Application

This is the main FastAPI application for the Core Engine service.
It handles AI orchestration, conversation management, and business logic.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from .core.config import settings
from .core.ai_orchestrator import AIOrchestrator
from .api.routes import ai_router
from .middleware.logging import setup_logging
from .middleware.metrics import add_prometheus_metrics

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    logger.info("Starting Core Engine Service...")
    
    # Initialize AI Orchestrator
    orchestrator = AIOrchestrator()
    await orchestrator.initialize()
    app.state.ai_orchestrator = orchestrator
    
    logger.info("Core Engine Service started successfully")
    yield
    
    # Cleanup
    logger.info("Shutting down Core Engine Service...")
    await orchestrator.cleanup()
    logger.info("Core Engine Service stopped")


# Create FastAPI application
app = FastAPI(
    title="Core Engine Service",
    description="AI orchestration and processing engine for AI Voice Agent platform",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Prometheus metrics if enabled
if settings.ENABLE_METRICS:
    add_prometheus_metrics(app)

# Include routers
app.include_router(ai_router, prefix="/api/v1", tags=["AI Processing"])


@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "Core Engine Service",
        "version": "1.0.0",
        "description": "AI orchestration and processing engine",
        "status": "operational",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "conversation": "/api/v1/conversation",
            "ai_processing": "/api/v1/ai"
        }
    }


@app.get("/health")
async def health_check():
    """Simple health check endpoint for container health checks."""
    try:
        orchestrator = app.state.ai_orchestrator
        status = await orchestrator.get_status()
        
        if status["initialized"]:
            return {"status": "healthy"}
        else:
            raise HTTPException(status_code=503, detail="Service not ready")
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")


@app.get("/status")
async def get_status():
    """Get detailed service status."""
    orchestrator = app.state.ai_orchestrator
    status = await orchestrator.get_status()
    
    return {
        "service": "core-engine",
        "status": "healthy" if status["initialized"] else "unhealthy",
        "version": "1.0.0",
        "orchestrator": status,
        "timestamp": status.get("timestamp")
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )