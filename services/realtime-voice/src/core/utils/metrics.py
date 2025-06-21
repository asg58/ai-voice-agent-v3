"""
Metrics Manager for AI Voice Agent
Handles metrics collection, monitoring, and reporting
"""
import logging
import time
from typing import Dict, Any

logger = logging.getLogger(__name__)

class MetricsManager:
    """Metrics manager for AI Voice Agent"""
    
    def __init__(self):
        """Initialize metrics manager"""
        self.initialized = False
        self.metrics = {}
        self.start_time = time.time()
    
    def initialize(self):
        """Initialize metrics manager"""
        logger.info("Initializing metrics manager")
        
        try:
            self.metrics = {
                "requests": 0,
                "audio_processed": 0,
                "transcriptions": 0,
                "responses_generated": 0,
                "errors": 0
            }
            self.initialized = True
            logger.info("Metrics manager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize metrics manager: {str(e)}")
            raise
    
    def increment(self, metric: str, value: int = 1):
        """Increment a metric"""
        if not self.initialized:
            return
        
        if metric in self.metrics:
            self.metrics[metric] += value
        else:
            self.metrics[metric] = value
    
    def record_timing(self, operation: str, duration_ms: float):
        """Record timing for an operation"""
        if not self.initialized:
            return
        
        metric_name = f"{operation}_ms"
        if metric_name in self.metrics:
            # Calculate running average
            count = self.metrics.get(f"{operation}_count", 0) + 1
            self.metrics[metric_name] = (self.metrics[metric_name] * (count - 1) + duration_ms) / count
            self.metrics[f"{operation}_count"] = count
        else:
            self.metrics[metric_name] = duration_ms
            self.metrics[f"{operation}_count"] = 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all metrics"""
        if not self.initialized:
            return {"status": "not_initialized"}
        
        # Add uptime
        uptime = time.time() - self.start_time
        return {
            "status": "ok",
            "uptime": uptime,
            **self.metrics
        }


# Create and initialize singleton instance
metrics_manager = MetricsManager()
metrics_manager.initialize()