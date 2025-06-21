"""
Dashboard models for Dashboard Service
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ServiceStatus(BaseModel):
    """
    Service status model.
    
    Attributes:
        id: Service ID
        name: Service name
        status: Service status
        host: Service host
        port: Service port
        last_heartbeat: Last heartbeat timestamp
        health_check_url: Health check URL
        metadata: Service metadata
    """
    id: str
    name: str
    status: str
    host: str
    port: int
    last_heartbeat: datetime
    health_check_url: str
    metadata: Dict[str, Any]


class SystemMetrics(BaseModel):
    """
    System metrics model.
    
    Attributes:
        cpu_usage: CPU usage percentage
        memory_usage: Memory usage percentage
        disk_usage: Disk usage percentage
        network_rx: Network receive bytes
        network_tx: Network transmit bytes
        timestamp: Metrics timestamp
    """
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_rx: int
    network_tx: int
    timestamp: datetime


class ServiceMetrics(BaseModel):
    """
    Service metrics model.
    
    Attributes:
        service_id: Service ID
        service_name: Service name
        request_count: Request count
        error_count: Error count
        average_response_time: Average response time
        timestamp: Metrics timestamp
    """
    service_id: str
    service_name: str
    request_count: int
    error_count: int
    average_response_time: float
    timestamp: datetime


class Alert(BaseModel):
    """
    Alert model.
    
    Attributes:
        id: Alert ID
        service_id: Service ID
        service_name: Service name
        level: Alert level
        message: Alert message
        timestamp: Alert timestamp
        acknowledged: Whether the alert is acknowledged
    """
    id: str
    service_id: str
    service_name: str
    level: str
    message: str
    timestamp: datetime
    acknowledged: bool


class DashboardSummary(BaseModel):
    """
    Dashboard summary model.
    
    Attributes:
        services: List of service statuses
        system_metrics: System metrics
        service_metrics: List of service metrics
        alerts: List of alerts
    """
    services: List[ServiceStatus]
    system_metrics: SystemMetrics
    service_metrics: List[ServiceMetrics]
    alerts: List[Alert]