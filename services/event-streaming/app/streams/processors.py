"""
Stream processors for the Event Streaming service.
"""
import logging
import time
from typing import Dict, Any, List
from ..models.event import Event, EventType

# Configure logging
logger = logging.getLogger("stream-processors")

def voice_analytics_processor(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Process voice events and generate analytics.
    
    Args:
        messages: List of voice events
        
    Returns:
        List[Dict[str, Any]]: List of analytics events
    """
    if not messages:
        return []
    
    results = []
    
    for message in messages:
        try:
            # Extract relevant data
            event_type = message.get("type")
            event_name = message.get("name")
            payload = message.get("payload", {})
            
            # Only process voice events
            if event_type != EventType.VOICE:
                continue
            
            # Create analytics event
            analytics_event = {
                "type": EventType.ANALYTICS,
                "name": f"voice_{event_name}_analytics",
                "topic": "analytics-events",
                "payload": {
                    "source_event_id": message.get("id"),
                    "source_event_type": event_type,
                    "source_event_name": event_name,
                    "timestamp": time.time(),
                    "metrics": {
                        "duration": payload.get("duration", 0),
                        "word_count": len(payload.get("transcript", "").split()),
                        "confidence": payload.get("confidence", 0)
                    }
                },
                "metadata": {
                    "source": "voice-analytics-processor",
                    "version": "1.0.0"
                }
            }
            
            results.append(analytics_event)
            logger.debug(f"Generated analytics event for voice event {message.get('id')}")
        except Exception as e:
            logger.error(f"Error processing voice event: {str(e)}")
    
    return results

def user_activity_processor(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Process user events and generate activity summaries.
    
    Args:
        messages: List of user events
        
    Returns:
        List[Dict[str, Any]]: List of activity summary events
    """
    if not messages:
        return []
    
    results = []
    
    for message in messages:
        try:
            # Extract relevant data
            event_type = message.get("type")
            event_name = message.get("name")
            payload = message.get("payload", {})
            
            # Only process user events
            if event_type != EventType.USER:
                continue
            
            # Create activity event
            activity_event = {
                "type": EventType.ANALYTICS,
                "name": "user_activity_summary",
                "topic": "analytics-events",
                "payload": {
                    "source_event_id": message.get("id"),
                    "user_id": payload.get("user_id"),
                    "activity_type": event_name,
                    "timestamp": time.time(),
                    "details": {
                        "duration": payload.get("duration", 0),
                        "action_count": payload.get("action_count", 1),
                        "session_id": payload.get("session_id")
                    }
                },
                "metadata": {
                    "source": "user-activity-processor",
                    "version": "1.0.0"
                }
            }
            
            results.append(activity_event)
            logger.debug(f"Generated activity summary for user event {message.get('id')}")
        except Exception as e:
            logger.error(f"Error processing user event: {str(e)}")
    
    return results

def system_health_processor(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Process system events and generate health metrics.
    
    Args:
        messages: List of system events
        
    Returns:
        List[Dict[str, Any]]: List of health metric events
    """
    if not messages:
        return []
    
    results = []
    
    for message in messages:
        try:
            # Extract relevant data
            event_type = message.get("type")
            event_name = message.get("name")
            payload = message.get("payload", {})
            
            # Only process system events
            if event_type != EventType.SYSTEM:
                continue
            
            # Create health event
            health_event = {
                "type": EventType.ANALYTICS,
                "name": "system_health_metrics",
                "topic": "analytics-events",
                "payload": {
                    "source_event_id": message.get("id"),
                    "service_name": payload.get("service_name"),
                    "timestamp": time.time(),
                    "metrics": {
                        "cpu_usage": payload.get("cpu_usage", 0),
                        "memory_usage": payload.get("memory_usage", 0),
                        "disk_usage": payload.get("disk_usage", 0),
                        "error_count": payload.get("error_count", 0),
                        "request_count": payload.get("request_count", 0),
                        "response_time": payload.get("response_time", 0)
                    }
                },
                "metadata": {
                    "source": "system-health-processor",
                    "version": "1.0.0"
                }
            }
            
            results.append(health_event)
            logger.debug(f"Generated health metrics for system event {message.get('id')}")
        except Exception as e:
            logger.error(f"Error processing system event: {str(e)}")
    
    return results

def register_processors(event_handler):
    """
    Register all stream processors with the event handler.
    
    Args:
        event_handler: The event handler instance
    """
    # Register voice analytics processor
    event_handler.register_stream_processor(
        input_topic="voice-events",
        output_topic="analytics-events",
        processor=voice_analytics_processor
    )
    
    # Register user activity processor
    event_handler.register_stream_processor(
        input_topic="user-events",
        output_topic="analytics-events",
        processor=user_activity_processor
    )
    
    # Register system health processor
    event_handler.register_stream_processor(
        input_topic="system-events",
        output_topic="analytics-events",
        processor=system_health_processor
    )