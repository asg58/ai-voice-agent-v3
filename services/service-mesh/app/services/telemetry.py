"""
Telemetry service for Service Mesh
"""
import uuid
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from loguru import logger
from app.models.telemetry import Span, Metric, LogEntry
from app.core.config import settings


class TelemetryService:
    """
    Telemetry service implementation.
    
    This class provides methods for collecting and reporting telemetry data.
    """
    
    def __init__(self):
        """Initialize the telemetry service."""
        self.spans = []
        self.metrics = []
        self.logs = []
        self.enabled = settings.TRACING_ENABLED
        
        logger.info(f"Telemetry service initialized (enabled={self.enabled})")
    
    def create_span(self, name: str, service_name: str, parent_id: Optional[str] = None) -> Span:
        """
        Create a new span.
        
        Args:
            name: Span name
            service_name: Service name
            parent_id: Parent span ID
            
        Returns:
            Span: New span
        """
        if not self.enabled:
            # Return a dummy span if tracing is disabled
            return Span(
                id="",
                trace_id="",
                parent_id=None,
                name=name,
                service_name=service_name,
                start_time=datetime.now(),
                end_time=None,
                duration_ms=None,
                tags={}
            )
        
        # Generate IDs
        span_id = str(uuid.uuid4())
        trace_id = str(uuid.uuid4()) if not parent_id else None
        
        # Create span
        span = Span(
            id=span_id,
            trace_id=trace_id,
            parent_id=parent_id,
            name=name,
            service_name=service_name,
            start_time=datetime.now(),
            end_time=None,
            duration_ms=None,
            tags={}
        )
        
        # Add span to list
        self.spans.append(span)
        
        logger.debug(f"Created span {span_id} for {name} in {service_name}")
        return span
    
    def end_span(self, span: Span):
        """
        End a span.
        
        Args:
            span: Span to end
        """
        if not self.enabled or not span.id:
            return
        
        # Set end time and duration
        span.end_time = datetime.now()
        span.duration_ms = (span.end_time - span.start_time).total_seconds() * 1000
        
        logger.debug(f"Ended span {span.id} for {span.name} in {span.service_name} ({span.duration_ms:.2f}ms)")
    
    def add_span_tag(self, span: Span, key: str, value: str):
        """
        Add a tag to a span.
        
        Args:
            span: Span to add tag to
            key: Tag key
            value: Tag value
        """
        if not self.enabled or not span.id:
            return
        
        span.tags[key] = value
    
    def record_metric(self, name: str, value: float, labels: Dict[str, str] = {}):
        """
        Record a metric.
        
        Args:
            name: Metric name
            value: Metric value
            labels: Metric labels
        """
        if not settings.METRICS_ENABLED:
            return
        
        # Create metric
        metric = Metric(
            name=name,
            value=value,
            timestamp=datetime.now(),
            labels=labels
        )
        
        # Add metric to list
        self.metrics.append(metric)
        
        logger.debug(f"Recorded metric {name}={value} with labels {labels}")
    
    def record_log(
        self,
        level: str,
        message: str,
        service_name: str,
        trace_id: Optional[str] = None,
        span_id: Optional[str] = None,
        metadata: Dict[str, Any] = {}
    ):
        """
        Record a log entry.
        
        Args:
            level: Log level
            message: Log message
            service_name: Service name
            trace_id: Trace ID
            span_id: Span ID
            metadata: Log metadata
        """
        # Create log entry
        log_entry = LogEntry(
            timestamp=datetime.now(),
            level=level,
            message=message,
            service_name=service_name,
            trace_id=trace_id,
            span_id=span_id,
            metadata=metadata
        )
        
        # Add log entry to list
        self.logs.append(log_entry)
        
        # Log the message
        logger.log(level, f"[{service_name}] {message}")
    
    def get_spans(self) -> List[Span]:
        """
        Get all spans.
        
        Returns:
            List[Span]: All spans
        """
        return self.spans
    
    def get_metrics(self) -> List[Metric]:
        """
        Get all metrics.
        
        Returns:
            List[Metric]: All metrics
        """
        return self.metrics
    
    def get_logs(self) -> List[LogEntry]:
        """
        Get all logs.
        
        Returns:
            List[LogEntry]: All logs
        """
        return self.logs