"""
Health check endpoints for the Real-time Voice AI Service
"""
from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter

from common.app.base.health import create_health_router
from ..core.config import settings

# Create health router
router = create_health_router(
    service_name=settings.APP_NAME,
    version=settings.APP_VERSION,
    start_time=datetime.now()
)

# Add custom endpoints
@router.get("/ai-status", summary="Get AI status")
async def get_ai_status():
    """
    Get the status of AI components
    
    Returns:
        Dict[str, Any]: AI components status
    """
    return {
        "status": "healthy",
        "components": {
            "speech_recognition": {
                "status": "healthy",
                "model": settings.STT_MODEL
            },
            "text_to_speech": {
                "status": "healthy",
                "model": settings.TTS_MODEL
            },
            "language_model": {
                "status": "healthy",
                "model": settings.OPENAI_MODEL
            }
        },
        "timestamp": datetime.now().isoformat()
    }