"""
Health check endpoints
"""
from fastapi import APIRouter
from app.models.edge_model import HealthResponse
from app.core.config import settings

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check() -> HealthResponse:
    """
    Health check endpoint.
    
    Returns:
        HealthResponse: Health status of the service
    """
    return HealthResponse(
        status="healthy",
        version=settings.APP_VERSION
    )