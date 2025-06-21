"""
Health Check Routes

Health check endpoints for the Core Engine service.
"""

from fastapi import APIRouter, Request
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "service": "core-engine",
        "version": "1.0.0"
    }


@router.get("/detailed")
async def detailed_health_check(request: Request) -> Dict[str, Any]:
    """Detailed health check with component status."""
    try:
        # Get AI orchestrator from app state
        orchestrator = getattr(request.app.state, 'ai_orchestrator', None)
        
        if orchestrator:
            orchestrator_status = await orchestrator.get_status()
        else:
            orchestrator_status = {"status": "not_initialized"}
        
        return {
            "status": "healthy",
            "service": "core-engine",
            "version": "1.0.0",
            "components": {
                "ai_orchestrator": orchestrator_status,
                "api": {"status": "healthy"},
                "dependencies": {
                    "openai": "connected" if orchestrator_status.get("initialized") else "disconnected",
                    "database": "connected",  # TODO: Add actual DB health check
                    "redis": "connected"      # TODO: Add actual Redis health check
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "core-engine",
            "version": "1.0.0",
            "error": str(e)
        }