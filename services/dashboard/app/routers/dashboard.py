"""
Dashboard router for Dashboard Service
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.models.user import User
from app.models.dashboard import DashboardSummary, ServiceStatus, SystemMetrics, ServiceMetrics, Alert
from app.services.auth import get_current_active_user
from app.services.dashboard import DashboardService
from loguru import logger

router = APIRouter()
dashboard_service = DashboardService()


@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary(current_user: User = Depends(get_current_active_user)):
    """
    Get dashboard summary.
    
    Args:
        current_user: Current user
        
    Returns:
        DashboardSummary: Dashboard summary
    """
    logger.info(f"User {current_user.username} requested dashboard summary")
    return await dashboard_service.get_dashboard_summary()


@router.get("/services", response_model=List[ServiceStatus])
async def get_services(current_user: User = Depends(get_current_active_user)):
    """
    Get all services.
    
    Args:
        current_user: Current user
        
    Returns:
        List[ServiceStatus]: List of service statuses
    """
    logger.info(f"User {current_user.username} requested services list")
    dashboard_summary = await dashboard_service.get_dashboard_summary()
    return dashboard_summary.services


@router.get("/services/{service_id}", response_model=ServiceStatus)
async def get_service(service_id: str, current_user: User = Depends(get_current_active_user)):
    """
    Get a specific service.
    
    Args:
        service_id: Service ID
        current_user: Current user
        
    Returns:
        ServiceStatus: Service status
        
    Raises:
        HTTPException: If the service is not found
    """
    logger.info(f"User {current_user.username} requested service {service_id}")
    service = await dashboard_service.service_discovery_client.get_service(service_id)
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service with ID {service_id} not found"
        )
    return service


@router.get("/metrics/system", response_model=SystemMetrics)
async def get_system_metrics(current_user: User = Depends(get_current_active_user)):
    """
    Get system metrics.
    
    Args:
        current_user: Current user
        
    Returns:
        SystemMetrics: System metrics
    """
    logger.info(f"User {current_user.username} requested system metrics")
    return await dashboard_service.metrics_service.get_system_metrics()


@router.get("/metrics/services", response_model=List[ServiceMetrics])
async def get_service_metrics(current_user: User = Depends(get_current_active_user)):
    """
    Get service metrics.
    
    Args:
        current_user: Current user
        
    Returns:
        List[ServiceMetrics]: List of service metrics
    """
    logger.info(f"User {current_user.username} requested service metrics")
    return await dashboard_service.metrics_service.get_service_metrics()


@router.get("/alerts", response_model=List[Alert])
async def get_alerts(current_user: User = Depends(get_current_active_user)):
    """
    Get alerts.
    
    Args:
        current_user: Current user
        
    Returns:
        List[Alert]: List of alerts
    """
    logger.info(f"User {current_user.username} requested alerts")
    return await dashboard_service.metrics_service.get_alerts()


@router.put("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str, current_user: User = Depends(get_current_active_user)):
    """
    Acknowledge an alert.
    
    Args:
        alert_id: Alert ID
        current_user: Current user
        
    Returns:
        dict: Acknowledgement status
        
    Raises:
        HTTPException: If the alert is not found
    """
    logger.info(f"User {current_user.username} acknowledged alert {alert_id}")
    # In a real implementation, this would update the alert in a database
    # For now, we'll just return a success message
    return {"status": "success", "message": f"Alert {alert_id} acknowledged"}