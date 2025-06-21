"""
Service API endpoints for the Service Discovery service.
"""
import logging
import time
import asyncio
import httpx
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from ..models.service import Service, ServiceCreate, ServiceUpdate, HealthCheck
from ..core.config import settings

# Configure logging
logger = logging.getLogger("service-api")

router = APIRouter(tags=["services"])

# In-memory service registry
# In a production environment, this would be stored in Redis or another database
services: Dict[str, Service] = {}

async def check_service_health(service_id: str) -> bool:
    """
    Check the health of a service.
    
    Args:
        service_id: The ID of the service to check
        
    Returns:
        bool: True if the service is healthy, False otherwise
    """
    service = services.get(service_id)
    if not service:
        return False
    
    try:
        url = f"http://{service.host}:{service.port}{service.health_check}"
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)
            
            if response.status_code == 200:
                # Update service status
                service.status = "healthy"
                service.last_check = time.time()
                service.last_seen = time.time()
                return True
            else:
                service.status = "unhealthy"
                service.last_check = time.time()
                return False
    except Exception as e:
        logger.error(f"Health check failed for service {service_id}: {str(e)}")
        service.status = "unhealthy"
        service.last_check = time.time()
        return False

async def health_check_worker():
    """Background worker to periodically check service health."""
    while True:
        try:
            for service_id in list(services.keys()):
                await check_service_health(service_id)
            
            # Clean up expired services
            current_time = time.time()
            expired_services = []
            
            for service_id, service in services.items():
                # If service hasn't been seen for TTL, mark it as expired
                if current_time - service.last_seen > settings.SERVICE_TTL:
                    expired_services.append(service_id)
            
            # Remove expired services
            for service_id in expired_services:
                logger.info(f"Removing expired service: {service_id}")
                del services[service_id]
        
        except Exception as e:
            logger.error(f"Error in health check worker: {str(e)}")
        
        # Wait for next check interval
        await asyncio.sleep(settings.HEALTH_CHECK_INTERVAL)

@router.get("", response_model=List[Service])
async def get_services():
    """
    Get all registered services.
    
    Returns:
        List[Service]: List of all registered services
    """
    return list(services.values())

@router.get("/{service_id}", response_model=Service)
async def get_service(service_id: str):
    """
    Get a service by ID.
    
    Args:
        service_id: The ID of the service
        
    Returns:
        Service: The service details
        
    Raises:
        HTTPException: If the service is not found
    """
    if service_id not in services:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service {service_id} not found"
        )
    
    return services[service_id]

@router.post("", response_model=Service, status_code=status.HTTP_201_CREATED)
async def register_service(service: ServiceCreate, background_tasks: BackgroundTasks):
    """
    Register a new service.
    
    Args:
        service: The service to register
        background_tasks: Background tasks runner
        
    Returns:
        Service: The registered service
        
    Raises:
        HTTPException: If the service ID is already registered
    """
    if service.id in services:
        # If service already exists, update it
        existing_service = services[service.id]
        existing_service.name = service.name
        existing_service.host = service.host
        existing_service.port = service.port
        existing_service.health_check = service.health_check
        existing_service.metadata = service.metadata
        existing_service.last_seen = time.time()
        
        # Check health in background
        background_tasks.add_task(check_service_health, service.id)
        
        return existing_service
    
    # Create new service
    new_service = Service(
        id=service.id,
        name=service.name,
        host=service.host,
        port=service.port,
        health_check=service.health_check,
        metadata=service.metadata,
        status="unknown",
        registered_at=time.time(),
        last_check=time.time(),
        last_seen=time.time()
    )
    
    services[service.id] = new_service
    
    # Check health in background
    background_tasks.add_task(check_service_health, service.id)
    
    logger.info(f"Registered new service: {service.id}")
    return new_service

@router.put("/{service_id}", response_model=Service)
async def update_service(service_id: str, service_update: ServiceUpdate):
    """
    Update a service.
    
    Args:
        service_id: The ID of the service to update
        service_update: The service update data
        
    Returns:
        Service: The updated service
        
    Raises:
        HTTPException: If the service is not found
    """
    if service_id not in services:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service {service_id} not found"
        )
    
    service = services[service_id]
    
    # Update fields if provided
    if service_update.name is not None:
        service.name = service_update.name
    
    if service_update.host is not None:
        service.host = service_update.host
    
    if service_update.port is not None:
        service.port = service_update.port
    
    if service_update.health_check is not None:
        service.health_check = service_update.health_check
    
    if service_update.status is not None:
        service.status = service_update.status
    
    if service_update.metadata is not None:
        service.metadata = service_update.metadata
    
    # Update last seen timestamp
    service.last_seen = time.time()
    
    logger.info(f"Updated service: {service_id}")
    return service

@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deregister_service(service_id: str):
    """
    Deregister a service.
    
    Args:
        service_id: The ID of the service to deregister
        
    Raises:
        HTTPException: If the service is not found
    """
    if service_id not in services:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service {service_id} not found"
        )
    
    del services[service_id]
    logger.info(f"Deregistered service: {service_id}")

@router.get("/{service_id}/health", response_model=HealthCheck)
async def check_health(service_id: str):
    """
    Check the health of a service.
    
    Args:
        service_id: The ID of the service to check
        
    Returns:
        HealthCheck: The health check result
        
    Raises:
        HTTPException: If the service is not found
    """
    if service_id not in services:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service {service_id} not found"
        )
    
    is_healthy = await check_service_health(service_id)
    service = services[service_id]
    
    return HealthCheck(
        status="healthy" if is_healthy else "unhealthy",
        details={
            "last_check": service.last_check,
            "last_seen": service.last_seen
        }
    )