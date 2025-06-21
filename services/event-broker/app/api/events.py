"""
Event API endpoints for the Event Broker Service
"""
import logging
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, status, BackgroundTasks, Path, Query
from pydantic import BaseModel

from ..models.event import Event, EventCreate, EventBatch, EventType
from ..handlers.event_handler import event_handler
from ..core.config import settings

# Configure logging
logger = logging.getLogger("events-api")

# Create router
router = APIRouter(prefix="/events", tags=["Events"])

class EventResponse(BaseModel):
    """Event response model"""
    id: str
    type: str
    name: str
    routing_key: str
    status: str
    timestamp: float
    message: str = "Event published successfully"

@router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED, summary="Publish event")
async def create_event(event_data: EventCreate, background_tasks: BackgroundTasks):
    """
    Create and publish a new event
    
    Args:
        event_data: The event data
        background_tasks: Background tasks runner
        
    Returns:
        EventResponse: The created event with status
    """
    # Create event object
    event = Event(**event_data.dict())
    
    # Publish event in background to avoid blocking
    def publish_event():
        success = event_handler.publish_event(event)
        if not success:
            logger.error(f"Failed to publish event {event.id}")
    
    background_tasks.add_task(publish_event)
    
    return EventResponse(
        id=event.id,
        type=event.type,
        name=event.name,
        routing_key=event.routing_key,
        status=event.status,
        timestamp=event.timestamp,
        message="Event published successfully"
    )

class EventBatchResponse(BaseModel):
    """Event batch response model"""
    count: int
    events: List[EventResponse]
    message: str = "Events published successfully"

@router.post("/batch", response_model=EventBatchResponse, status_code=status.HTTP_201_CREATED, summary="Publish event batch")
async def create_events_batch(batch: EventBatch, background_tasks: BackgroundTasks):
    """
    Create and publish a batch of events
    
    Args:
        batch: The batch of events
        background_tasks: Background tasks runner
        
    Returns:
        EventBatchResponse: The created events with status
    """
    events = []
    event_responses = []
    
    for event_data in batch.events:
        # Create event object
        event = Event(**event_data.dict())
        events.append(event)
        
        event_responses.append(
            EventResponse(
                id=event.id,
                type=event.type,
                name=event.name,
                routing_key=event.routing_key,
                status=event.status,
                timestamp=event.timestamp,
                message="Event queued for publishing"
            )
        )
    
    # Publish events in background
    def publish_events():
        for event in events:
            success = event_handler.publish_event(event)
            if not success:
                logger.error(f"Failed to publish event {event.id}")
    
    background_tasks.add_task(publish_events)
    
    return EventBatchResponse(
        count=len(events),
        events=event_responses,
        message=f"Batch of {len(events)} events queued for publishing"
    )

@router.get("/queues", response_model=Dict[str, Dict[str, Any]], summary="Get predefined queues")
async def get_queues():
    """
    Get all predefined queues
    
    Returns:
        Dict[str, Dict[str, Any]]: The predefined queues
    """
    return settings.PREDEFINED_QUEUES

@router.get("/types", response_model=List[str], summary="Get event types")
async def get_event_types():
    """
    Get all available event types
    
    Returns:
        List[str]: The available event types
    """
    return [event_type.value for event_type in EventType]

class QueueStatsResponse(BaseModel):
    """Queue statistics response model"""
    queue_name: str
    message_count: int
    consumer_count: int
    routing_key: str
    is_durable: bool

@router.get("/stats", response_model=List[QueueStatsResponse], summary="Get queue statistics")
async def get_queue_stats():
    """
    Get statistics for all queues
    
    Returns:
        List[QueueStatsResponse]: Queue statistics
    """
    stats = event_handler.get_queue_stats()
    
    return [
        QueueStatsResponse(
            queue_name=queue_name,
            message_count=stats.get("message_count", 0),
            consumer_count=stats.get("consumer_count", 0),
            routing_key=stats.get("routing_key", ""),
            is_durable=stats.get("is_durable", False)
        )
        for queue_name, stats in stats.items()
    ]