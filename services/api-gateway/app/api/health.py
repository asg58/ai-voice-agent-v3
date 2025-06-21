"""
Health check endpoints for the API Gateway
"""
from datetime import datetime
import logging
from typing import Dict, Any, List
from fastapi import APIRouter, Request

from common.app.base.health import create_health_router
from ..core.config import settings
from ..services.service_discovery import service_discovery

# Configure logging
logger = logging.getLogger(f"{settings.APP_NAME}.api.health")

# Create health router
router = create_health_router(
    service_name=settings.APP_NAME,
    version=settings.APP_VERSION,
    start_time=datetime.now()
)

# Add custom endpoints
@router.get("/services", summary="Get services health")
async def services_health(request: Request):
    """
    Check the health of all services
    
    Args:
        request: The incoming request
        
    Returns:
        Dict[str, Any]: Services health status
    """
    client_ip = request.client.host if request.client else "unknown"
    logger.info(f"Services health check request from {client_ip}")
    services = await service_discovery.get_all_services()
    
    services_health = []
    for service in services:
        service_id = service.get("id")
        if not service_id:
            logger.warning("Skipping service with missing ID in health check")
            continue
            
        try:
            is_healthy = await service_discovery.check_health(service_id)
            
            services_health.append({
                "id": service_id,
                "name": service.get("name", service_id),
                "status": "healthy" if is_healthy else "unhealthy",
                "host": service.get("host"),
                "port": service.get("port")
            })
        except Exception as e:
            logger.error(f"Error checking health for service {service_id}: {str(e)}")
            services_health.append({
                "id": service_id,
                "name": service.get("name", service_id),
                "status": "unknown",
                "host": service.get("host"),
                "port": service.get("port"),
                "error": str(e)
            })
    
    # Determine overall status
    overall_status = "healthy"
    unhealthy_count = 0
    unknown_count = 0
    unhealthy_services = []
    unknown_services = []
    
    for service in services_health:
        if service["status"] == "unhealthy":
            unhealthy_count += 1
            unhealthy_services.append(service["id"])
        elif service["status"] == "unknown":
            unknown_count += 1
            unknown_services.append(service["id"])
            
    # If any services are unhealthy or unknown, the status is degraded
    if unhealthy_count > 0 or unknown_count > 0:
        overall_status = "degraded"
    
    # If all services are unhealthy, the status is critical
    if (unhealthy_count + unknown_count) == len(services_health) and len(services_health) > 0:
        overall_status = "critical"
        logger.warning(f"All services are unhealthy or unknown: {len(services_health)} services down")
    elif unhealthy_count > 0 or unknown_count > 0:
        logger.warning(
            f"Some services are not healthy: {unhealthy_count} unhealthy, {unknown_count} unknown "
            f"out of {len(services_health)} services"
        )
    
    return {
        "status": overall_status,
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "services": services_health,
        "healthy_count": len(services_health) - unhealthy_count - unknown_count,
        "unhealthy_count": unhealthy_count,
        "unknown_count": unknown_count,
        "unhealthy_services": unhealthy_services if unhealthy_count > 0 else None,
        "unknown_services": unknown_services if unknown_count > 0 else None,
        "total_count": len(services_health),
        "timestamp": datetime.now().isoformat()
    }