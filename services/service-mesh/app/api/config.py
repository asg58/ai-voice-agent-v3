"""
Configuration API endpoints for Service Mesh
"""
from fastapi import APIRouter, Depends, HTTPException
from app.models.mesh import MeshConfig, ServiceConfig
from app.services.config_loader import ConfigLoader
from app.services.router import Router
from loguru import logger
from app.dependencies import get_config_loader, get_router

router = APIRouter()


@router.get("/config", response_model=MeshConfig)
async def get_config(config_loader: ConfigLoader = Depends(get_config_loader)):
    """
    Get the mesh configuration.
    
    Returns:
        MeshConfig: Mesh configuration
    """
    config = config_loader.load_config()
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    return config


@router.get("/config/services", response_model=list[ServiceConfig])
async def get_services(config_loader: ConfigLoader = Depends(get_config_loader)):
    """
    Get all service configurations.
    
    Returns:
        list[ServiceConfig]: List of service configurations
    """
    config = config_loader.load_config()
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    return config.services


@router.get("/config/services/{service_name}", response_model=ServiceConfig)
async def get_service(service_name: str, config_loader: ConfigLoader = Depends(get_config_loader)):
    """
    Get a specific service configuration.
    
    Args:
        service_name: Service name
        
    Returns:
        ServiceConfig: Service configuration
    """
    config = config_loader.load_config()
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    
    for service in config.services:
        if service.name == service_name:
            return service
    
    raise HTTPException(status_code=404, detail=f"Service {service_name} not found")


@router.get("/config/routes", response_model=None)
async def get_routes(router_service: Router = Depends(get_router)) -> list[dict]:
    """
    Get all routes.

    Returns:
        list[dict]: List of routes as dictionaries
    """
    routes = list(router_service.routes.values())
    # Convert Pydantic models to dictionaries to avoid serialization issues
    route_dicts = []
    for route in routes:
        try:
            route_dicts.append(route.dict())
        except Exception as e:
            # Handle any serialization errors
            logger.error(f"Serialization error for route {route}: {e}")
    return route_dicts