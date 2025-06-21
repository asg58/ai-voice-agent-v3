"""
Event handlers for the Event Broker service.
"""
import logging
import json
import time
from typing import Dict, Any, Optional, List, Callable
from pika.adapters.blocking_connection import BlockingChannel
from pika.spec import Basic, BasicProperties
from ..core.rabbitmq import rabbitmq_client
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
        exchange: Optional[str] = None,
        routing_key: Optional[str] = None
    ) -> bool:
        """
        Publish an event to RabbitMQ.
        
        Args:
            event: The event to publish
            exchange: The exchange to publish to (default: settings.DEFAULT_EXCHANGE)
            routing_key: The routing key (default: event.routing_key)
            
        Returns:
            bool: True if published successfully, False otherwise
        """
        # Validate the event
        if not self.validate_event(event):
            logger.error(f"Event validation failed for {event.type}:{event.name}")
            return False
        
        # Use default exchange if not specified
        if not exchange:
            exchange = settings.DEFAULT_EXCHANGE
        
        # Use event routing key if not specified
        if not routing_key:
            routing_key = event.routing_key
        
        # Convert event to dictionary
        event_dict = event.dict()
        
        # Set message properties based on priority
        properties = BasicProperties(
            delivery_mode=2,  # Persistent
            content_type='application/json',
            timestamp=int(time.time()),
            priority=self._get_priority_value(event.priority),
            message_id=event.id,
            type=f"{event.type}.{event.name}",
            headers={
                "x-event-type": event.type,
                "x-event-name": event.name,
                "x-retry-count": event.retry_count
            }
        )
        
        # Publish the event
        return rabbitmq_client.publish(
            exchange=exchange,
            routing_key=routing_key,
            body=event_dict,
            properties=properties
        )
    
    def _get_priority_value(self, priority: EventPriority) -> int:
        """
        Convert priority enum to integer value.
        
        Args:
            priority: The priority enum
            
        Returns:
            int: The priority value (0-9)
        """
        priority_map = {
            EventPriority.LOW: 1,
            EventPriority.MEDIUM: 5,
            EventPriority.HIGH: 7,
            EventPriority.CRITICAL: 9
        }
        return priority_map.get(priority, 5)
    
    def handle_message(
        self,
        channel: BlockingChannel,
        method: Basic.Deliver,
        properties: BasicProperties,
        body: bytes
    ):
        """
        Handle a message from RabbitMQ.
        
        Args:
            channel: The channel
            method: The delivery method
            properties: The message properties
            body: The message body
        """
        try:
            # Parse message body
            message = json.loads(body.decode('utf-8'))
            
            # Create event object
            event = Event(**message)
            
            # Update event status
            event.status = EventStatus.PROCESSING
            
            # Process the event
            success = self.process_event(event)
            
            if success:
                # Update event status
                event.status = EventStatus.COMPLETED
                
                # Acknowledge the message
                channel.basic_ack(delivery_tag=method.delivery_tag)
                logger.info(f"Successfully processed event {event.id}")
            else:
                # Update event status
                event.status = EventStatus.FAILED
                
                # Increment retry count
                event.retry_count += 1
                
                # Check if we should retry
                if event.retry_count < 3:  # Max retries
                    # Reject and requeue
                    channel.basic_reject(delivery_tag=method.delivery_tag, requeue=True)
                    logger.warning(f"Failed to process event {event.id}, requeuing (retry {event.retry_count})")
                else:
                    # Reject without requeuing (will go to dead letter queue)
                    channel.basic_reject(delivery_tag=method.delivery_tag, requeue=False)
                    logger.error(f"Failed to process event {event.id} after {event.retry_count} retries, sending to dead letter queue")
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
            # Reject without requeuing in case of parsing/handling errors
            channel.basic_reject(delivery_tag=method.delivery_tag, requeue=False)
    
    def start_consuming(self, queues: Optional[List[str]] = None):
        """
        Start consuming messages from queues.
        
        Args:
            queues: List of queues to consume from (default: all predefined queues)
        """
        if not queues:
            queues = list(settings.PREDEFINED_QUEUES.keys())
        
        for queue in queues:
            rabbitmq_client.consume(
                queue=queue,
                callback=self.handle_message,
                auto_ack=False
            )
        
        # Start consuming
        rabbitmq_client.start_consuming()
    
    def stop_consuming(self):
        """Stop consuming messages."""
        rabbitmq_client.stop_consuming()

# Create global event handler
event_handler = EventHandler()