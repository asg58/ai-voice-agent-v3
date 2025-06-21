"""
Health check endpoints for the Event Broker Service
"""
from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter

from common.app.base.health import create_health_router
from ..core.config import settings
from ..core.rabbitmq import rabbitmq_client

# Create health router
router = create_health_router(
    service_name=settings.APP_NAME,
    version=settings.APP_VERSION,
    start_time=datetime.now()
)

# Add custom endpoints
@router.get("/rabbitmq", summary="Get RabbitMQ status")
async def rabbitmq_status():
    """
    Get the status of the RabbitMQ connection
    
    Returns:
        Dict[str, Any]: RabbitMQ connection status
    """
    # Check RabbitMQ connection
    rabbitmq_healthy = rabbitmq_client.connection and rabbitmq_client.connection.is_open
    
    return {
        "status": "healthy" if rabbitmq_healthy else "unhealthy",
        "service": settings.APP_NAME,
        "dependencies": {
            "rabbitmq": {
                "status": "healthy" if rabbitmq_healthy else "unhealthy",
                "host": settings.RABBITMQ_HOST,
                "port": settings.RABBITMQ_PORT,
                "vhost": settings.RABBITMQ_VHOST
            }
        },
        "timestamp": datetime.now().isoformat()
    }