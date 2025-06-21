"""
Event handlers for the Event Streaming service.
"""
import logging
import json
import time
from typing import Dict, Any, Optional, List, Callable
from ..core.kafka import kafka_client
from ..core.config import settings
from ..models.event import Event, EventType, EventPriority, EventStatus

# Configure logging
logger = logging.getLogger("event-handler")

class EventHandler:
    """
    Handler for processing events.
    """
    def __init__(self):
        self.event_processors = {}
        self.schema_validators = {}
        self.stream_processors = {}
    
    def register_processor(
        self,
        event_type: EventType,
        event_name: str,
        processor: Callable[[Event], None]
    ):
        """
        Register a processor for a specific event type and name.
        
        Args:
            event_type: The type of event
            event_name: The name of the event
            processor: The processor function
        """
        key = f"{event_type}:{event_name}"
        self.event_processors[key] = processor
        logger.info(f"Registered processor for event {key}")
    
    def register_schema_validator(
        self,
        event_type: EventType,
        event_name: str,
        validator: Callable[[Dict[str, Any]], bool]
    ):
        """
        Register a schema validator for a specific event type and name.
        
        Args:
            event_type: The type of event
            event_name: The name of the event
            validator: The validator function
        """
        key = f"{event_type}:{event_name}"
        self.schema_validators[key] = validator
        logger.info(f"Registered schema validator for event {key}")
    
    def register_stream_processor(
        self,
        input_topic: str,
        output_topic: str,
        processor: Callable[[List[Dict[str, Any]]], List[Dict[str, Any]]]
    ):
        """
        Register a stream processor for a specific input and output topic.
        
        Args:
            input_topic: The input topic
            output_topic: The output topic
            processor: The processor function
        """
        key = f"{input_topic}:{output_topic}"
        self.stream_processors[key] = processor
        logger.info(f"Registered stream processor for {key}")
    
    def validate_event(self, event: Event) -> bool:
        """
        Validate an event against its schema.
        
        Args:
            event: The event to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not settings.SCHEMA_VALIDATION_ENABLED:
            return True
        
        key = f"{event.type}:{event.name}"
        validator = self.schema_validators.get(key)
        
        if validator:
            try:
                return validator(event.payload)
            except Exception as e:
                logger.error(f"Schema validation error for event {key}: {str(e)}")
                return False
        
        # No validator found, assume valid
        return True
    
    def process_event(self, event: Event) -> bool:
        """
        Process an event.
        
        Args:
            event: The event to process
            
        Returns:
            bool: True if processed successfully, False otherwise
        """
        key = f"{event.type}:{event.name}"
        processor = self.event_processors.get(key)
        
        if processor:
            try:
                processor(event)
                return True
            except Exception as e:
                logger.error(f"Error processing event {key}: {str(e)}")
                return False
        
        # No processor found, log and return True (considered handled)
        logger.warning(f"No processor found for event {key}")
        return True
    
    def publish_event(
        self,
        event: Event,
        topic: Optional[str] = None,
        key: Optional[str] = None,
        headers: Optional[List[tuple]] = None
    ) -> bool:
        """
        Publish an event to Kafka.
        
        Args:
            event: The event to publish
            topic: The topic to publish to (default: event.topic)
            key: Optional message key
            headers: Optional message headers
            
        Returns:
            bool: True if published successfully, False otherwise
        """
        # Validate the event
        if not self.validate_event(event):
            logger.error(f"Event validation failed for {event.type}:{event.name}")
            return False
        
        # Use event topic if not specified
        if not topic:
            topic = event.topic
        
        # Publish the event
        return kafka_client.publish(
            topic=topic,
            event=event,
            key=key,
            headers=headers
        )
    
    def handle_message(self, message: Dict[str, Any]):
        """
        Handle a message from Kafka.
        
        Args:
            message: The message to handle
        """
        try:
            # Create event object
            event = Event(**message)
            
            # Update event status
            event.status = EventStatus.PROCESSING
            
            # Process the event
            success = self.process_event(event)
            
            if success:
                # Update event status
                event.status = EventStatus.COMPLETED
                logger.info(f"Successfully processed event {event.id}")
            else:
                # Update event status
                event.status = EventStatus.FAILED
                logger.error(f"Failed to process event {event.id}")
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
    
    def start_consuming(self, topics: Optional[List[str]] = None):
        """
        Start consuming messages from topics.
        
        Args:
            topics: List of topics to consume from (default: all predefined topics)
        """
        if not topics:
            topics = list(settings.PREDEFINED_TOPICS.keys())
        
        # Start consumer for each topic
        for topic in topics:
            kafka_client.start_consumer(
                topics=[topic],
                handler=self.handle_message,
                group_id=f"{settings.KAFKA_CONSUMER_GROUP}-{topic}"
            )
    
    def stop_consuming(self):
        """Stop consuming messages."""
        kafka_client.stop_all_consumers()
    
    def start_stream_processing(self):
        """Start stream processing."""
        if not settings.STREAM_PROCESSING_ENABLED:
            logger.info("Stream processing is disabled")
            return
        
        # Start stream processors
        for key, processor in self.stream_processors.items():
            input_topic, output_topic = key.split(":")
            
            # Create a handler for this stream processor
            def create_stream_handler(processor, output_topic):
                def handler(message):
                    try:
                        # Process the message
                        result = processor([message])
                        
                        # Publish results
                        for item in result:
                            event = Event(**item)
                            self.publish_event(event, topic=output_topic)
                    except Exception as e:
                        logger.error(f"Error in stream processor: {str(e)}")
                
                return handler
            
            # Start consumer for this stream processor
            kafka_client.start_consumer(
                topics=[input_topic],
                handler=create_stream_handler(processor, output_topic),
                group_id=f"{settings.KAFKA_CONSUMER_GROUP}-stream-{input_topic}-{output_topic}"
            )
            
            logger.info(f"Started stream processor for {input_topic} -> {output_topic}")

# Create global event handler
event_handler = EventHandler()