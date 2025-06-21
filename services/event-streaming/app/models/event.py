"""
Event models for the Event Streaming service.
"""
import uuid
import time
from typing import Dict, Any, Optional, List
from enum import Enum
from pydantic import BaseModel, Field, validator

class EventType(str, Enum):
    """Event types."""
    VOICE = "voice"
    USER = "user"
    SYSTEM = "system"
    NOTIFICATION = "notification"
    ANALYTICS = "analytics"
    CUSTOM = "custom"

class EventPriority(str, Enum):
    """Event priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class EventStatus(str, Enum):
    """Event status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class EventBase(BaseModel):
    """Base event model."""
    type: EventType
    name: str
    topic: str
    payload: Dict[str, Any]
    priority: EventPriority = EventPriority.MEDIUM
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class EventCreate(EventBase):
    """Event creation model."""
    pass

class Event(EventBase):
    """Event model."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = Field(default_factory=time.time)
    status: EventStatus = EventStatus.PENDING
    retry_count: int = 0
    
    @validator("topic")
    def validate_topic(cls, v, values):
        """Validate topic format."""
        if not v:
            event_type = values.get("type", EventType.CUSTOM)
            return f"{event_type}-events"
        return v

class EventInTopic(Event):
    """Event as stored in the topic."""
    partition: Optional[int] = None
    offset: Optional[int] = None
    
    class Config:
        orm_mode = True

class EventBatch(BaseModel):
    """Batch of events."""
    events: List[EventCreate]
    
    @validator("events")
    def validate_events(cls, v):
        """Validate that the batch is not empty."""
        if not v:
            raise ValueError("Event batch cannot be empty")
        return v

class EventSchema(BaseModel):
    """Event schema model."""
    name: str
    version: str
    schema: Dict[str, Any]
    
    class Config:
        orm_mode = True

class TopicInfo(BaseModel):
    """Topic information model."""
    name: str
    partitions: int
    replication_factor: int
    config: Dict[str, Any]
    
    class Config:
        orm_mode = True

class ConsumerGroupInfo(BaseModel):
    """Consumer group information model."""
    group_id: str
    topics: List[str]
    members: int
    
    class Config:
        orm_mode = True