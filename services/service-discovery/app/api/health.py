"""
Health check endpoints for the Service Discovery Service
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
@router.get("/services-status", summary="Get services status")
async def services_status():
    """
    Get the status of all registered services
    
    Returns:
        Dict[str, Any]: Services status
    """
    from ..api.services import services
    
    service_count = len(services)
    healthy_count = sum(1 for service in services.values() if service.status == "healthy")
    
    return {
        "status": "healthy" if service_count == 0 or healthy_count / service_count >= 0.5 else "degraded",
        "service": settings.APP_NAME,
        "services": {
            "total": service_count,
            "healthy": healthy_count,
            "unhealthy": service_count - healthy_count
        },
        "timestamp": datetime.now().isoformat()
    }