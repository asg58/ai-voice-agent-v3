"""
Event API endpoints for the Event Streaming service.
"""
import logging
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from ..models.event import Event, EventCreate, EventBatch, TopicInfo
from ..handlers.event_handler import event_handler
from ..core.kafka import kafka_client
from ..core.config import settings

# Configure logging
logger = logging.getLogger("events-api")

router = APIRouter(prefix="/events", tags=["events"])

@router.post("", response_model=Event, status_code=status.HTTP_201_CREATED)
async def create_event(event_data: EventCreate, background_tasks: BackgroundTasks):
    """
    Create and publish a new event.
    
    Args:
        event_data: The event data
        background_tasks: Background tasks runner
        
    Returns:
        Event: The created event
    """
    # Create event object
    event = Event(**event_data.dict())
    
    # Publish event in background to avoid blocking
    def publish_event():
        success = event_handler.publish_event(event)
        if not success:
            logger.error(f"Failed to publish event {event.id}")
    
    background_tasks.add_task(publish_event)
    
    return event

@router.post("/batch", response_model=List[Event], status_code=status.HTTP_201_CREATED)
async def create_events_batch(batch: EventBatch, background_tasks: BackgroundTasks):
    """
    Create and publish a batch of events.
    
    Args:
        batch: The batch of events
        background_tasks: Background tasks runner
        
    Returns:
        List[Event]: The created events
    """
    events = []
    
    for event_data in batch.events:
        # Create event object
        event = Event(**event_data.dict())
        events.append(event)
    
    # Publish events in background
    def publish_events():
        for event in events:
            success = event_handler.publish_event(event)
            if not success:
                logger.error(f"Failed to publish event {event.id}")
    
    background_tasks.add_task(publish_events)
    
    return events

@router.get("/topics", response_model=List[str])
async def get_topics():
    """
    Get all topics.
    
    Returns:
        List[str]: List of topic names
    """
    return kafka_client.list_topics()

@router.get("/topics/{topic_name}", response_model=TopicInfo)
async def get_topic(topic_name: str):
    """
    Get topic information.
    
    Args:
        topic_name: The name of the topic
        
    Returns:
        TopicInfo: The topic information
        
    Raises:
        HTTPException: If the topic is not found
    """
    topics = kafka_client.list_topics()
    
    if topic_name not in topics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Topic {topic_name} not found"
        )
    
    # Get topic config from settings if available
    topic_config = settings.PREDEFINED_TOPICS.get(topic_name, {})
    
    return TopicInfo(
        name=topic_name,
        partitions=topic_config.get("partitions", 3),
        replication_factor=topic_config.get("replication_factor", 1),
        config=topic_config.get("config", {})
    )

@router.post("/topics", response_model=TopicInfo, status_code=status.HTTP_201_CREATED)
async def create_topic(topic_info: TopicInfo):
    """
    Create a new topic.
    
    Args:
        topic_info: The topic information
        
    Returns:
        TopicInfo: The created topic information
        
    Raises:
        HTTPException: If the topic already exists or creation fails
    """
    topics = kafka_client.list_topics()
    
    if topic_info.name in topics:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Topic {topic_info.name} already exists"
        )
    
    success = kafka_client.create_topic(
        topic_name=topic_info.name,
        partitions=topic_info.partitions,
        replication_factor=topic_info.replication_factor,
        config=topic_info.config
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create topic {topic_info.name}"
        )
    
    return topic_info

@router.delete("/topics/{topic_name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_topic(topic_name: str):
    """
    Delete a topic.
    
    Args:
        topic_name: The name of the topic
        
    Raises:
        HTTPException: If the topic is not found or deletion fails
    """
    topics = kafka_client.list_topics()
    
    if topic_name not in topics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Topic {topic_name} not found"
        )
    
    # Check if it's a predefined topic
    if topic_name in settings.PREDEFINED_TOPICS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete predefined topic {topic_name}"
        )
    
    success = kafka_client.delete_topic(topic_name)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete topic {topic_name}"
        )