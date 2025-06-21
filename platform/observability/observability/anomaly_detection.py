"""
AI-powered anomaly detection module for system behavior analysis.
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class AnomalyDetection:
    """
    AI-powered anomaly detection for system behavior monitoring.
    
    This class uses AI techniques to detect anomalies in system behavior
    and provides insights into potential issues.
    """
    
    def __init__(self, threshold: float = 0.5):
        """
        Initialize the anomaly detection system.
        
        Args:
            threshold: Anomaly detection threshold (0.0 to 1.0)
        """
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("Threshold must be between 0.0 and 1.0")
            
        self.threshold = threshold
        self.detection_history = []
        logger.info(f"Anomaly detection system initialized with threshold: {threshold}")
    
    def detect_anomalies(self, system_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use AI to detect anomalies in system behavior.
        
        Args:
            system_data: Dictionary containing system metrics and data
            
        Returns:
            Dictionary containing anomaly detection results
            
        Raises:
            ValueError: If system_data is empty or None
            TypeError: If system_data is not a dictionary
        """
        if not system_data:
            raise ValueError("System data cannot be empty or None")
        
        if not isinstance(system_data, dict):
            raise TypeError("System data must be a dictionary")
        
        try:
            detection_time = datetime.now()
            anomalies_found = []
            
            # Mock AI-based anomaly detection logic
            for metric_name, metric_value in system_data.items():
                if isinstance(metric_value, (int, float)):
                    # Simple mock anomaly detection based on threshold
                    if metric_value > 80:  # Mock: values above 80 are anomalous
                        anomalies_found.append({
                            "metric": metric_name,
                            "value": metric_value,
                            "severity": "high" if metric_value > 95 else "medium",
                            "description": f"Unusual {metric_name} value detected",
                            "timestamp": detection_time.isoformat()
                        })
            
            # Calculate anomaly score
            anomaly_score = len(anomalies_found) / len(system_data) if system_data else 0
            
            result = {
                "timestamp": detection_time.isoformat(),
                "anomaly_score": round(anomaly_score, 3),
                "threshold": self.threshold,
                "anomalies_count": len(anomalies_found),
                "anomalies": anomalies_found,
                "status": "anomalies_detected" if anomalies_found else "normal",
                "system_health": "degraded" if anomaly_score > self.threshold else "healthy"
            }
            
            # Store in history
            self.detection_history.append(result)
            
            # Keep only last 100 detections to prevent memory issues
            if len(self.detection_history) > 100:
                self.detection_history = self.detection_history[-100:]
            
            logger.info(f"Anomaly detection completed: {len(anomalies_found)} anomalies found")
            return result
            
        except Exception as e:
            error_msg = f"Error during anomaly detection: {str(e)}"
            logger.error(error_msg)
            return {
                "timestamp": datetime.now().isoformat(),
                "anomaly_score": 0,
                "threshold": self.threshold,
                "anomalies_count": 0,
                "anomalies": [],
                "status": "error",
                "error": error_msg
            }
    
    def get_detection_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent anomaly detection history.
        
        Args:
            limit: Maximum number of results to return
            
        Returns:
            List of recent detection results
        """
        return self.detection_history[-limit:] if self.detection_history else []
    
    def update_threshold(self, new_threshold: float) -> bool:
        """
        Update the anomaly detection threshold.
        
        Args:
            new_threshold: New threshold value (0.0 to 1.0)
            
        Returns:
            True if updated successfully, False otherwise
        """
        try:
            if not 0.0 <= new_threshold <= 1.0:
                raise ValueError("Threshold must be between 0.0 and 1.0")
            
            old_threshold = self.threshold
            self.threshold = new_threshold
            logger.info(f"Threshold updated from {old_threshold} to {new_threshold}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update threshold: {str(e)}")
            return False
