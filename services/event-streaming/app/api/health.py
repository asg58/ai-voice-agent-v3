"""
Health check API endpoints for the Event Streaming service.
"""
import time
import platform
import psutil
from fastapi import APIRouter
from ..core.config import settings
from ..core.kafka import kafka_client

router = APIRouter(prefix="/health", tags=["health"])

@router.get("")
async def health_check():
    """
    Check the health of the Event Streaming service.
    
    Returns:
        dict: Health status
    """
    # Check Kafka connection
    kafka_healthy = len(kafka_client.list_topics()) > 0
    
    return {
        "status": "healthy" if kafka_healthy else "degraded",
        "service": "event-streaming",
        "version": "1.0.0",
        "timestamp": time.time(),
        "dependencies": {
            "kafka": "healthy" if kafka_healthy else "unhealthy"
        }
    }

@router.get("/system")
async def system_health():
    """
    Check the health of the system.
    
    Returns:
        dict: System health status
    """
    return {
        "status": "healthy",
        "service": "event-streaming",
        "system": {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage("/").percent,
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "uptime": time.time() - psutil.boot_time()
        },
        "timestamp": time.time()
    }

@router.get("/kafka")
async def kafka_health():
    """
    Check the health of Kafka.
    
    Returns:
        dict: Kafka health status
    """
    topics = kafka_client.list_topics()
    
    return {
        "status": "healthy" if topics else "unhealthy",
        "service": "event-streaming",
        "kafka": {
            "bootstrap_servers": settings.KAFKA_BOOTSTRAP_SERVERS,
            "topics": topics,
            "topic_count": len(topics)
        },
        "timestamp": time.time()
    }