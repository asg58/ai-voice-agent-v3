"""
Event models for the Event Broker Service
"""
import uuid
import time
from typing import Dict, Any, Optional, List
from enum import Enum
from pydantic import BaseModel, Field, validator

class EventType(str, Enum):
    """Event types"""
    VOICE = "voice"
    USER = "user"
    SYSTEM = "system"
    NOTIFICATION = "notification"
    CUSTOM = "custom"

class EventPriority(str, Enum):
    """Event priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class EventStatus(str, Enum):
    """Event status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class EventBase(BaseModel):
    """Base event model"""
    type: EventType = Field(..., description="Event type")
    name: str = Field(..., description="Event name")
    routing_key: str = Field(..., description="Routing key for the event")
    payload: Dict[str, Any] = Field(..., description="Event payload")
    priority: EventPriority = Field(default=EventPriority.MEDIUM, description="Event priority")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")

class EventCreate(EventBase):
    """Event creation model"""
    
    class Config:
        json_schema_extra = {
            "example": {
                "type": "voice",
                "name": "speech_recognized",
                "routing_key": "events.voice.speech_recognized",
                "payload": {
                    "session_id": "123456",
                    "text": "Hello, how can I help you?",
                    "confidence": 0.95
                },
                "priority": "medium",
                "metadata": {
                    "user_id": "user123",
                    "source": "web"
                }
            }
        }

class Event(EventBase):
    """Event model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Event ID")
    timestamp: float = Field(default_factory=time.time, description="Event timestamp")
    status: EventStatus = Field(default=EventStatus.PENDING, description="Event status")
    retry_count: int = Field(default=0, description="Number of retry attempts")
    
    @validator("routing_key")
    def validate_routing_key(cls, v, values):
        """Validate routing key format"""
        if not v:
            event_type = values.get("type", EventType.CUSTOM)
            event_name = values.get("name", "event")
            return f"events.{event_type}.{event_name}"
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "timestamp": 1623456789.123,
                "type": "voice",
                "name": "speech_recognized",
                "routing_key": "events.voice.speech_recognized",
                "payload": {
                    "session_id": "123456",
                    "text": "Hello, how can I help you?",
                    "confidence": 0.95
                },
                "priority": "medium",
                "status": "pending",
                "retry_count": 0,
                "metadata": {
                    "user_id": "user123",
                    "source": "web"
                }
            }
        }

class EventInQueue(Event):
    """Event as stored in the queue"""
    queue: str = Field(..., description="Queue name")
    exchange: str = Field(..., description="Exchange name")
    delivery_tag: Optional[int] = Field(None, description="Delivery tag")

class EventBatch(BaseModel):
    """Batch of events"""
    events: List[EventCreate] = Field(..., description="List of events to create")
    
    @validator("events")
    def validate_events(cls, v):
        """Validate that the batch is not empty"""
        if not v:
            raise ValueError("Event batch cannot be empty")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "events": [
                    {
                        "type": "voice",
                        "name": "speech_recognized",
                        "routing_key": "events.voice.speech_recognized",
                        "payload": {
                            "session_id": "123456",
                            "text": "Hello, how can I help you?",
                            "confidence": 0.95
                        },
                        "priority": "medium",
                        "metadata": {
                            "user_id": "user123",
                            "source": "web"
                        }
                    },
                    {
                        "type": "system",
                        "name": "service_started",
                        "routing_key": "events.system.service_started",
                        "payload": {
                            "service_id": "voice-service",
                            "timestamp": 1623456789.123
                        },
                        "priority": "low",
                        "metadata": {}
                    }
                ]
            }
        }

class EventSchema(BaseModel):
    """Event schema model"""
    name: str = Field(..., description="Schema name")
    version: str = Field(..., description="Schema version")
    schema: Dict[str, Any] = Field(..., description="JSON schema definition")