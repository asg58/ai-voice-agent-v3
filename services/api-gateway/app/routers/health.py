"""
Health check router for the API Gateway.
"""
import time
import platform
import logging
import psutil
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, Request
from ..core.config import settings
from ..services.service_discovery import service_discovery

# Configure logging
logger = logging.getLogger(f"{settings.APP_NAME}.routers.health")

router = APIRouter(prefix="/health", tags=["health"])

async def get_system_info() -> Dict[str, Any]:
    """
    Get system information.
    
    Returns:
        Dict[str, Any]: System information
    """
    # Get disk usage for the root path, handling different OS paths
    root_path = "C:\\" if platform.system() == "Windows" else "/"
    
    try:
        disk_usage = psutil.disk_usage(root_path)
        disk_percent = disk_usage.percent
    except Exception as e:
        # Fallback if we can't get disk usage for the root path
        logger.warning(f"Failed to get disk usage for {root_path}: {str(e)}")
        disk_percent = None
    
    # Get CPU usage with a small timeout
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
    except Exception:
        cpu_percent = None
    
    # Get memory usage
    try:
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_info = {
            "total": memory.total,
            "available": memory.available,
            "used": memory.used,
            "percent": memory.percent
        }
    except Exception:
        memory_percent = None
        memory_info = None
    
    # Get uptime
    try:
        uptime = time.time() - psutil.boot_time()
    except Exception:
        uptime = None
    
    return {
        "cpu_percent": cpu_percent,
        "memory_percent": memory_percent,
        "memory_info": memory_info,
        "disk_percent": disk_percent,
        "platform": platform.platform(),
        "system": platform.system(),
        "release": platform.release(),
        "python_version": platform.python_version(),
        "uptime": uptime
    }

async def get_services_health() -> List[Dict[str, Any]]:
    """
    Get health status of all services.
    
    Returns:
        List[Dict[str, Any]]: Health status of all services
    """
    result = []
    
    try:
        # Ensure service discovery client is initialized
        client_initialized = await service_discovery._ensure_client()
        if not client_initialized:
            logger.warning("Service discovery client not initialized in health check")
            return [{
                "id": "service-discovery",
                "name": "Service Discovery",
                "status": "unknown",
                "error": "Service discovery client not initialized"
            }]
        
        # Get all services
        services = await service_discovery.get_all_services()
        
        # If no services found, return a warning
        if not services:
            logger.warning("No services found in service discovery")
            return [{
                "id": "service-discovery",
                "name": "Service Discovery",
                "status": "degraded",
                "error": "No services found"
            }]
        
        # Check health of each service
        for service in services:
            service_id = service.get("id")
            if not service_id:
                logger.warning("Skipping service with missing ID in health check")
                continue
                
            try:
                is_healthy = await service_discovery.check_health(service_id)
                
                result.append({
                    "id": service_id,
                    "name": service.get("name", service_id),
                    "status": "healthy" if is_healthy else "unhealthy",
                    "host": service.get("host"),
                    "port": service.get("port")
                })
            except Exception as e:
                logger.error(f"Error checking health for service {service_id}: {str(e)}")
                result.append({
                    "id": service_id,
                    "name": service.get("name", service_id),
                    "status": "unknown",
                    "host": service.get("host"),
                    "port": service.get("port"),
                    "error": str(e)
                })
    except Exception as e:
        logger.error(f"Error getting services from service discovery: {str(e)}")
        result.append({
            "id": "service-discovery",
            "name": "Service Discovery",
            "status": "unhealthy",
            "error": str(e)
        })
    
    return result

@router.get("")
async def health_check(request: Request):
    """
    Check the health of the API Gateway.
    
    Args:
        request: The incoming request
        
    Returns:
        Dict[str, Any]: Health status
    """
    try:
        client_ip = request.client.host if request.client else "unknown"
    except Exception:
        client_ip = "unknown"
    logger.info(f"Health check request from {client_ip}")
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": time.time()
    }

@router.get("/system")
async def system_health(request: Request):
    """
    Check the health of the system.
    
    Args:
        request: The incoming request
        
    Returns:
        Dict[str, Any]: System health status
    """
    try:
        client_ip = request.client.host if request.client else "unknown"
    except Exception:
        client_ip = "unknown"
    logger.info(f"System health check request from {client_ip}")
    system_info = await get_system_info()
    
    # Determine system health based on resource usage
    status = "healthy"
    
    # Check CPU usage
    if system_info.get("cpu_percent") is not None and system_info["cpu_percent"] > 90:
        status = "warning"
    
    # Check memory usage
    if system_info.get("memory_percent") is not None and system_info["memory_percent"] > 90:
        status = "warning"
    
    # Check disk usage
    if system_info.get("disk_percent") is not None and system_info["disk_percent"] > 90:
        status = "warning"
    
    return {
        "status": status,
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "system": system_info,
        "timestamp": time.time()
    }

@router.get("/services")
async def services_health(request: Request):
    """
    Check the health of all services.
    
    Args:
        request: The incoming request
        
    Returns:
        Dict[str, Any]: Services health status
    """
    try:
        client_ip = request.client.host if request.client else "unknown"
    except Exception:
        client_ip = "unknown"
    logger.info(f"Services health check request from {client_ip}")
    services_health = await get_services_health()
    
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
            logger.warning(f"Service {service['id']} is unhealthy")
        elif service["status"] == "unknown":
            unknown_count += 1
            unknown_services.append(service["id"])
            logger.warning(f"Service {service['id']} status is unknown")
    
    # If any services are unhealthy or unknown, the status is degraded
    if unhealthy_count > 0 or unknown_count > 0:
        overall_status = "degraded"
    
    # If all services are unhealthy or unknown, the status is critical
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
        "timestamp": time.time()
    }