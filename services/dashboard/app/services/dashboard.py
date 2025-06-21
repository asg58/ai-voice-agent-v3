"""
Dashboard service for Dashboard Service
"""
from typing import List, Dict, Any, Optional
from loguru import logger
from app.models.dashboard import DashboardSummary
from app.services.service_discovery import ServiceDiscoveryClient
from app.services.metrics import MetricsService


class DashboardService:
    """
    Service for retrieving and processing dashboard data.
    
    This class provides methods for retrieving dashboard summary data.
    """
    
    def __init__(self):
        """Initialize the Dashboard service."""
        self.service_discovery_client = ServiceDiscoveryClient()
        self.metrics_service = MetricsService(self.service_discovery_client)
        logger.info("Dashboard service initialized")
    
    async def get_dashboard_summary(self) -> DashboardSummary:
        """
        Get dashboard summary.
        
        Returns:
            DashboardSummary: Dashboard summary
        """
        # Get services
        services = await self.service_discovery_client.get_all_services()
        
        # Get system metrics
        system_metrics = await self.metrics_service.get_system_metrics()
        
        # Get service metrics
        service_metrics = await self.metrics_service.get_service_metrics()
        
        # Get alerts
        alerts = await self.metrics_service.get_alerts()
        
        # Create dashboard summary
        dashboard_summary = DashboardSummary(
            services=services,
            system_metrics=system_metrics,
            service_metrics=service_metrics,
            alerts=alerts
        )
        
        return dashboard_summary