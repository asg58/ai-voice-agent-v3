"""
Advanced Monitoring and Metrics for Voice AI Service
Real-time performance tracking with Prometheus integration
"""
import time
import asyncio
import logging
import psutil
from typing import Dict, Any, List
from collections import defaultdict, deque
from dataclasses import dataclass

try:
    from prometheus_client import Counter, Histogram, Gauge, generate_latest
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    
logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetric:
    name: str
    value: float
    timestamp: float
    labels: Dict[str, str] = None

class VoiceAIMetrics:
    """
    Comprehensive metrics collection for Voice AI service
    Tracks performance, errors, and system health
    """
    
    def __init__(self, enable_prometheus: bool = True):
        self.enable_prometheus = enable_prometheus and PROMETHEUS_AVAILABLE
        
        # Performance tracking
        self.metrics_history = defaultdict(lambda: deque(maxlen=1000))
        self.alert_thresholds = {}
        self.active_alerts = set()
        
        # Initialize Prometheus metrics if available
        if self.enable_prometheus:
            self._init_prometheus_metrics()
            
        # System metrics
        self.system_stats = {
            "start_time": time.time(),
            "total_requests": 0,
            "total_errors": 0,
            "peak_memory_usage": 0,
            "peak_cpu_usage": 0
        }
        
    def _init_prometheus_metrics(self):
        """Initialize Prometheus metrics"""
        # Request metrics
        self.http_requests_total = Counter(
            'voice_ai_http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status']
        )
        
        self.websocket_connections_total = Gauge(
            'voice_ai_websocket_connections_active',
            'Active WebSocket connections'
        )
        
        # Audio processing metrics
        self.audio_processing_duration = Histogram(
            'voice_ai_audio_processing_seconds',
            'Audio processing duration',
            ['model_type', 'language']
        )
        
        self.transcription_accuracy = Histogram(
            'voice_ai_transcription_accuracy',
            'Transcription accuracy score',
            ['language', 'model']
        )
        
        # Response time metrics
        self.response_latency = Histogram(
            'voice_ai_response_latency_seconds',
            'End-to-end response latency',
            ['operation_type']
        )
        
        # Error metrics
        self.errors_total = Counter(
            'voice_ai_errors_total',
            'Total errors by type',
            ['error_type', 'component']
        )
        
        # System resource metrics
        self.cpu_usage = Gauge(
            'voice_ai_cpu_usage_percent',
            'CPU usage percentage'
        )
        
        self.memory_usage = Gauge(
            'voice_ai_memory_usage_bytes',
            'Memory usage in bytes'
        )
        
        self.gpu_memory_usage = Gauge(
            'voice_ai_gpu_memory_usage_bytes',
            'GPU memory usage in bytes'
        )
        
        # Business metrics
        self.active_sessions = Gauge(
            'voice_ai_active_sessions',
            'Number of active conversation sessions'
        )
        
        self.messages_per_second = Gauge(
            'voice_ai_messages_per_second',
            'Messages processed per second'
        )
        
        # Model performance
        self.model_load_time = Histogram(
            'voice_ai_model_load_seconds',
            'Model loading time',
            ['model_name', 'model_type']
        )
        
        self.inference_time = Histogram(
            'voice_ai_inference_seconds',
            'Model inference time',
            ['model_name', 'input_size']
        )
        
    def record_http_request(self, method: str, endpoint: str, status: int, duration: float):
        """Record HTTP request metrics"""
        self.system_stats["total_requests"] += 1
        
        if self.enable_prometheus:
            self.http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status=str(status)
            ).inc()
            
        # Track response times
        self.metrics_history["http_response_time"].append(
            PerformanceMetric(
                name="http_response_time",
                value=duration,
                timestamp=time.time(),
                labels={"method": method, "endpoint": endpoint}
            )
        )
        
    def record_websocket_connection(self, action: str, session_count: int):
        """Record WebSocket connection metrics"""
        if self.enable_prometheus:
            if action == "connect":
                self.websocket_connections_total.inc()
            elif action == "disconnect":
                self.websocket_connections_total.dec()
            else:
                self.websocket_connections_total.set(session_count)
                
    def record_audio_processing(self, duration: float, model_type: str, language: str):
        """Record audio processing metrics"""
        if self.enable_prometheus:
            self.audio_processing_duration.labels(
                model_type=model_type,
                language=language
            ).observe(duration)
            
        self.metrics_history["audio_processing"].append(
            PerformanceMetric(
                name="audio_processing_time",
                value=duration,
                timestamp=time.time(),
                labels={"model_type": model_type, "language": language}
            )
        )
        
    def record_transcription_accuracy(self, accuracy: float, language: str, model: str):
        """Record transcription accuracy metrics"""
        if self.enable_prometheus:
            self.transcription_accuracy.labels(
                language=language,
                model=model
            ).observe(accuracy)
            
    def record_response_latency(self, latency: float, operation_type: str):
        """Record end-to-end response latency"""
        if self.enable_prometheus:
            self.response_latency.labels(
                operation_type=operation_type
            ).observe(latency)
            
        self.metrics_history["response_latency"].append(
            PerformanceMetric(
                name="response_latency",
                value=latency,
                timestamp=time.time(),
                labels={"operation": operation_type}
            )
        )
        
    def record_error(self, error_type: str, component: str):
        """Record error occurrence"""
        self.system_stats["total_errors"] += 1
        
        if self.enable_prometheus:
            self.errors_total.labels(
                error_type=error_type,
                component=component
            ).inc()
            
        # Check for error rate alerts
        self._check_error_rate_alert()
        
    def record_model_performance(self, model_name: str, model_type: str, load_time: float = None, inference_time: float = None, input_size: str = None):
        """Record model performance metrics"""
        if load_time is not None and self.enable_prometheus:
            self.model_load_time.labels(
                model_name=model_name,
                model_type=model_type
            ).observe(load_time)
            
        if inference_time is not None and self.enable_prometheus:
            self.inference_time.labels(
                model_name=model_name,
                input_size=input_size or "unknown"
            ).observe(inference_time)
            
    def update_system_metrics(self):
        """Update system resource metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=None)
            if self.enable_prometheus:
                self.cpu_usage.set(cpu_percent)
            self.system_stats["peak_cpu_usage"] = max(
                self.system_stats["peak_cpu_usage"], cpu_percent
            )
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_bytes = memory.used
            if self.enable_prometheus:
                self.memory_usage.set(memory_bytes)
            self.system_stats["peak_memory_usage"] = max(
                self.system_stats["peak_memory_usage"], memory_bytes
            )
            
            # GPU memory (if available)
            try:
                import GPUtil
                gpus = GPUtil.getGPUs()
                if gpus and self.enable_prometheus:
                    gpu_memory = gpus[0].memoryUsed * 1024 * 1024  # Convert MB to bytes
                    self.gpu_memory_usage.set(gpu_memory)
            except ImportError:
                pass
                
            # Check system health alerts
            self._check_system_health_alerts(cpu_percent, memory.percent)
            
        except Exception as e:
            logger.error(f"Error updating system metrics: {e}")
            
    def set_alert_threshold(self, metric_name: str, threshold: float, comparison: str = "greater"):
        """Set alert threshold for a metric"""
        self.alert_thresholds[metric_name] = {
            "threshold": threshold,
            "comparison": comparison
        }
        
    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status"""
        current_time = time.time()
        uptime = current_time - self.system_stats["start_time"]
        
        # Calculate averages for recent metrics
        recent_window = 300  # 5 minutes
        recent_metrics = {}
        
        for metric_name, history in self.metrics_history.items():
            recent_values = [
                m.value for m in history
                if current_time - m.timestamp <= recent_window
            ]
            
            if recent_values:
                recent_metrics[metric_name] = {
                    "average": sum(recent_values) / len(recent_values),
                    "min": min(recent_values),
                    "max": max(recent_values),
                    "count": len(recent_values)
                }
                
        return {
            "status": "healthy" if not self.active_alerts else "warning",
            "uptime_seconds": uptime,
            "active_alerts": list(self.active_alerts),
            "system_stats": self.system_stats,
            "recent_metrics": recent_metrics,
            "prometheus_enabled": self.enable_prometheus,
            "timestamp": current_time
        }
        
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary for the last hour"""
        current_time = time.time()
        hour_ago = current_time - 3600
        
        summary = {
            "time_range": "last_hour",
            "metrics": {}
        }
        
        for metric_name, history in self.metrics_history.items():
            hour_values = [
                m.value for m in history
                if m.timestamp >= hour_ago
            ]
            
            if hour_values:
                summary["metrics"][metric_name] = {
                    "count": len(hour_values),
                    "average": sum(hour_values) / len(hour_values),
                    "min": min(hour_values),
                    "max": max(hour_values),
                    "p50": self._percentile(hour_values, 50),
                    "p95": self._percentile(hour_values, 95),
                    "p99": self._percentile(hour_values, 99)
                }
                
        return summary
        
    def export_prometheus_metrics(self) -> str:
        """Export metrics in Prometheus format"""
        if not self.enable_prometheus:
            return "# Prometheus not available"
            
        try:
            return generate_latest().decode('utf-8')
        except Exception as e:
            logger.error(f"Error generating Prometheus metrics: {e}")
            return f"# Error generating metrics: {e}"
            
    def _check_error_rate_alert(self):
        """Check if error rate exceeds threshold"""
        current_time = time.time()
        minute_ago = current_time - 60
        
        # Count errors in last minute
        recent_errors = sum(
            1 for metric in self.metrics_history.get("errors", [])
            if metric.timestamp >= minute_ago
        )
        
        # Count total requests in last minute
        recent_requests = sum(
            1 for metric in self.metrics_history.get("http_response_time", [])
            if metric.timestamp >= minute_ago
        )
        
        if recent_requests > 0:
            error_rate = recent_errors / recent_requests
            if error_rate > 0.1:  # 10% error rate threshold
                alert_id = "high_error_rate"
                if alert_id not in self.active_alerts:
                    self.active_alerts.add(alert_id)
                    logger.warning(f"High error rate alert: {error_rate:.2%}")
            else:
                self.active_alerts.discard("high_error_rate")
                
    def _check_system_health_alerts(self, cpu_percent: float, memory_percent: float):
        """Check system health and trigger alerts if needed"""
        # CPU usage alert
        if cpu_percent > 80:
            alert_id = "high_cpu_usage"
            if alert_id not in self.active_alerts:
                self.active_alerts.add(alert_id)
                logger.warning(f"High CPU usage: {cpu_percent:.1f}%")
        else:
            self.active_alerts.discard("high_cpu_usage")
            
        # Memory usage alert
        if memory_percent > 85:
            alert_id = "high_memory_usage"
            if alert_id not in self.active_alerts:
                self.active_alerts.add(alert_id)
                logger.warning(f"High memory usage: {memory_percent:.1f}%")
        else:
            self.active_alerts.discard("high_memory_usage")
            
    @staticmethod
    def _percentile(values: List[float], percentile: int) -> float:
        """Calculate percentile of values"""
        if not values:
            return 0.0
            
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]

# Global metrics instance
voice_ai_metrics = VoiceAIMetrics()

# Background task for system metrics
async def metrics_collector():
    """Background task to collect system metrics"""
    while True:
        try:
            voice_ai_metrics.update_system_metrics()
            await asyncio.sleep(30)  # Update every 30 seconds
        except Exception as e:
            logger.error(f"Error in metrics collector: {e}")
            await asyncio.sleep(60)  # Back off on error
