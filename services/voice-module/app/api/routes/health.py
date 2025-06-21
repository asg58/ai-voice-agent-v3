"""
Health Check Routes for Voice Module

Health check endpoints for the Voice Module service.
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
        "service": "voice-module",
        "version": "1.0.0"
    }


@router.get("/detailed")
async def detailed_health_check(request: Request) -> Dict[str, Any]:
    """Detailed health check with component status."""
    try:
        # Get voice processor from app state
        voice_processor = getattr(request.app.state, 'voice_processor', None)
        websocket_manager = getattr(request.app.state, 'websocket_manager', None)

        if voice_processor:
            processor_status = await voice_processor.get_status()
        else:
            processor_status = {"status": "not_initialized"}

        if websocket_manager:
            ws_status = await websocket_manager.get_status()
        else:
            ws_status = {"status": "not_initialized", "connections": 0}

        return {
            "status": "healthy",
            "service": "voice-module",
            "version": "1.0.0",
            "components": {
                "voice_processor": processor_status,
                "websocket_manager": ws_status,
                "capabilities": {
                    "speech_to_text": processor_status.get("components", {}).get("whisper", {}).get("available", False),
                    "text_to_speech": processor_status.get("components", {}).get("tts", {}).get("available", False),
                    "voice_activity_detection": processor_status.get("components", {}).get("vad", {}).get("available", False),       
                    "real_time_processing": True,
                    "websocket_streaming": True
                }
            },
            "statistics": processor_status.get("statistics", {}),
            "active_connections": ws_status.get("connections", 0)
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "voice-module",
            "version": "1.0.0",
            "error": str(e)
        }