"""
Telemetry models for Service Mesh
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class Span(BaseModel):
    """
    Span model for distributed tracing.
    
    Attributes:
        id: Span ID
        trace_id: Trace ID
        parent_id: Parent span ID
        name: Span name
        service_name: Service name
        start_time: Start time
        end_time: End time
        duration_ms: Duration in milliseconds
        tags: Span tags
    """
    id: str
    trace_id: str
    parent_id: Optional[str] = None
    name: str
    service_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    tags: Dict[str, str] = {}


class Metric(BaseModel):
    """
    Metric model.
    
    Attributes:
        name: Metric name
        value: Metric value
        timestamp: Metric timestamp
        labels: Metric labels
    """
    name: str
    value: float
    timestamp: datetime
    labels: Dict[str, str] = {}


class LogEntry(BaseModel):
    """
    Log entry model.
    
    Attributes:
        timestamp: Log timestamp
        level: Log level
        message: Log message
        service_name: Service name
        trace_id: Trace ID
        span_id: Span ID
        metadata: Log metadata
    """
    timestamp: datetime
    level: str
    message: str
    service_name: str
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    metadata: Dict[str, Any] = {}