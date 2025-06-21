"""
Health router for Dashboard Service
"""
from fastapi import APIRouter
from app.core.config import settings
from loguru import logger

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        dict: Health status
    """
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION
    }