"""
Event Publisher for Realtime Voice Service

Publishes events to RabbitMQ and Kafka for integration with other services.
"""
import json
import logging
import time
import uuid
from typing import Dict, Any, Optional, List, Union
import asyncio
import aio_pika
from aiokafka import AIOKafkaProducer

from src.config import settings
from src.models import ConversationSession, ConversationMessage

logger = logging.getLogger(__name__)


class EventPublisher:
    """
    Event publisher for Realtime Voice Service
    
    Publishes events to RabbitMQ and Kafka for integration with other services.
    """
    
    def __init__(self):
        """Initialize event publisher"""
        self.rabbitmq_connection = None
        self.rabbitmq_channel = None
        self.kafka_producer = None
        self.is_initialized = False
        self.service_name = "realtime-voice"
        self.exchange_name = "voice_events"
        self.kafka_topic_prefix = "voice."
        
        # Event schemas
        self.event_schemas = {
            "session_created": ["session_id", "user_id", "language"],
            "session_ended": ["session_id", "duration"],
            "transcription_created": ["session_id", "text", "confidence"],
            "response_generated": ["session_id", "text"],
            "speech_synthesized": ["session_id", "duration", "voice_id"],
            "intent_detected": ["session_id", "intent", "confidence", "entities"],
            "error_occurred": ["session_id", "error_type", "error_message"]
        }
    
    async def initialize(self) -> bool:
        """
        Initialize connections to RabbitMQ and Kafka
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:            # Initialize RabbitMQ connection
            if settings.rabbitmq_enabled:
                await self._init_rabbitmq()
            
            # Initialize Kafka connection
            if settings.kafka_enabled:
                await self._init_kafka()
            
            self.is_initialized = True
            logger.info("Event publisher initialized successfully")
            return True
        
        except Exception as e:
            logger.error(f"Failed to initialize event publisher: {e}")
            return False
    
    async def _init_rabbitmq(self):
        """Initialize RabbitMQ connection and channel"""
        try:            # Create connection
            self.rabbitmq_connection = await aio_pika.connect_robust(
                host=settings.rabbitmq_host,
                port=settings.rabbitmq_port,
                login=settings.rabbitmq_user,
                password=settings.rabbitmq_password,
                virtualhost=settings.rabbitmq_vhost
            )
            
            # Create channel
            self.rabbitmq_channel = await self.rabbitmq_connection.channel()
            
            # Declare exchange
            await self.rabbitmq_channel.declare_exchange(
                name=self.exchange_name,
                type=aio_pika.ExchangeType.TOPIC,
                durable=True
            )
            
            logger.info("RabbitMQ connection established")
        
        except Exception as e:
            logger.error(f"Failed to initialize RabbitMQ connection: {e}")
            self.rabbitmq_connection = None
            self.rabbitmq_channel = None
            raise
    
    async def _init_kafka(self):
        """Initialize Kafka producer"""
        try:
            # Create Kafka producer
            self.kafka_producer = AIOKafkaProducer(
                bootstrap_servers=settings.kafka_bootstrap_servers,
                client_id=f"{self.service_name}-{uuid.uuid4()}",
                acks="all",
                enable_idempotence=True,
                compression_type="gzip",
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            
            # Start producer
            await self.kafka_producer.start()
            
            logger.info("Kafka producer initialized")
        
        except Exception as e:
            logger.error(f"Failed to initialize Kafka producer: {e}")
            self.kafka_producer = None
            raise
    
    async def publish_event(self, event_type: str, payload: Dict[str, Any]) -> bool:
        """
        Publish event to RabbitMQ and Kafka
        
        Args:
            event_type: Type of event
            payload: Event payload
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_initialized:
            logger.warning("Event publisher not initialized")
            return False
        
        try:
            # Validate event payload
            if not self._validate_event(event_type, payload):
                logger.warning(f"Invalid event payload for {event_type}: {payload}")
                return False
            
            # Create event message
            event_message = self._create_event_message(event_type, payload)
            
            # Publish to RabbitMQ
            rabbitmq_result = await self._publish_to_rabbitmq(event_type, event_message)
            
            # Publish to Kafka
            kafka_result = await self._publish_to_kafka(event_type, event_message)
            
            return rabbitmq_result or kafka_result
        
        except Exception as e:
            logger.error(f"Failed to publish event {event_type}: {e}")
            return False
    
    def _validate_event(self, event_type: str, payload: Dict[str, Any]) -> bool:
        """
        Validate event payload against schema
        
        Args:
            event_type: Type of event
            payload: Event payload
            
        Returns:
            bool: True if valid, False otherwise
        """
        # Check if event type is supported
        if event_type not in self.event_schemas:
            logger.warning(f"Unsupported event type: {event_type}")
            return False
        
        # Check required fields
        required_fields = self.event_schemas[event_type]
        for field in required_fields:
            if field not in payload:
                logger.warning(f"Missing required field '{field}' for event {event_type}")
                return False
        
        return True
    
    def _create_event_message(self, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create event message with metadata
        
        Args:
            event_type: Type of event
            payload: Event payload
            
        Returns:
            dict: Event message with metadata
        """
        return {
            "id": str(uuid.uuid4()),
            "type": event_type,
            "source": self.service_name,
            "time": time.time(),
            "payload": payload
        }
    
    async def _publish_to_rabbitmq(self, event_type: str, event_message: Dict[str, Any]) -> bool:
        """
        Publish event to RabbitMQ
        
        Args:
            event_type: Type of event
            event_message: Event message
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.rabbitmq_channel or not settings.rabbitmq_enabled:
            return False
        
        try:
            # Create routing key
            routing_key = f"{self.service_name}.{event_type}"
            
            # Create message
            message = aio_pika.Message(
                body=json.dumps(event_message).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                content_type="application/json",
                headers={
                    "event_type": event_type,
                    "source": self.service_name
                }
            )
            
            # Get exchange
            exchange = await self.rabbitmq_channel.get_exchange(self.exchange_name)
            
            # Publish message
            await exchange.publish(message, routing_key=routing_key)
            
            logger.debug(f"Published event {event_type} to RabbitMQ")
            return True
        
        except Exception as e:
            logger.error(f"Failed to publish event {event_type} to RabbitMQ: {e}")
            return False
    
    async def _publish_to_kafka(self, event_type: str, event_message: Dict[str, Any]) -> bool:
        """
        Publish event to Kafka
        
        Args:
            event_type: Type of event
            event_message: Event message
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.kafka_producer or not settings.kafka_enabled:
            return False
        
        try:
            # Create topic
            topic = f"{self.kafka_topic_prefix}{event_type}"
            
            # Publish message
            await self.kafka_producer.send_and_wait(
                topic=topic,
                value=event_message,
                key=event_message.get("payload", {}).get("session_id", "").encode()
            )
            
            logger.debug(f"Published event {event_type} to Kafka")
            return True
        
        except Exception as e:
            logger.error(f"Failed to publish event {event_type} to Kafka: {e}")
            return False
    
    async def publish_session_created(self, session: ConversationSession) -> bool:
        """
        Publish session created event
        
        Args:
            session: Conversation session
            
        Returns:
            bool: True if successful, False otherwise
        """
        payload = {
            "session_id": session.session_id,
            "user_id": session.user_id or "anonymous",
            "language": session.language,
            "created_at": session.started_at.isoformat() if hasattr(session, "started_at") else time.time(),
            "metadata": session.context or {}
        }
        
        return await self.publish_event("session_created", payload)
    
    async def publish_session_ended(self, session: ConversationSession) -> bool:
        """
        Publish session ended event
        
        Args:
            session: Conversation session
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Calculate duration
        if hasattr(session, "started_at") and hasattr(session, "last_activity"):
            duration = (session.last_activity - session.started_at).total_seconds()
        else:
            duration = 0
        
        payload = {
            "session_id": session.session_id,
            "user_id": session.user_id or "anonymous",
            "duration": duration,
            "message_count": len(session.messages) if hasattr(session, "messages") else 0,
            "ended_at": time.time()
        }
        
        return await self.publish_event("session_ended", payload)
    
    async def publish_transcription_created(self, session_id: str, text: str, confidence: float, 
                                           language: Optional[str] = None) -> bool:
        """
        Publish transcription created event
        
        Args:
            session_id: Session ID
            text: Transcribed text
            confidence: Confidence score
            language: Detected language
            
        Returns:
            bool: True if successful, False otherwise
        """
        payload = {
            "session_id": session_id,
            "text": text,
            "confidence": confidence,
            "language": language or "unknown",
            "timestamp": time.time()
        }
        
        return await self.publish_event("transcription_created", payload)
    
    async def publish_response_generated(self, session_id: str, text: str, 
                                        intent: Optional[str] = None) -> bool:
        """
        Publish response generated event
        
        Args:
            session_id: Session ID
            text: Generated response text
            intent: Detected intent
            
        Returns:
            bool: True if successful, False otherwise
        """
        payload = {
            "session_id": session_id,
            "text": text,
            "intent": intent,
            "timestamp": time.time()
        }
        
        return await self.publish_event("response_generated", payload)
    
    async def publish_speech_synthesized(self, session_id: str, text: str, duration: float, 
                                        voice_id: str) -> bool:
        """
        Publish speech synthesized event
        
        Args:
            session_id: Session ID
            text: Synthesized text
            duration: Audio duration in seconds
            voice_id: Voice ID used
            
        Returns:
            bool: True if successful, False otherwise
        """
        payload = {
            "session_id": session_id,
            "text": text,
            "duration": duration,
            "voice_id": voice_id,
            "timestamp": time.time()
        }
        
        return await self.publish_event("speech_synthesized", payload)
    
    async def publish_intent_detected(self, session_id: str, intent: str, confidence: float, 
                                     entities: Optional[List[Dict[str, Any]]] = None) -> bool:
        """
        Publish intent detected event
        
        Args:
            session_id: Session ID
            intent: Detected intent
            confidence: Confidence score
            entities: Extracted entities
            
        Returns:
            bool: True if successful, False otherwise
        """
        payload = {
            "session_id": session_id,
            "intent": intent,
            "confidence": confidence,
            "entities": entities or [],
            "timestamp": time.time()
        }
        
        return await self.publish_event("intent_detected", payload)
    
    async def publish_error_occurred(self, session_id: str, error_type: str, 
                                    error_message: str) -> bool:
        """
        Publish error occurred event
        
        Args:
            session_id: Session ID
            error_type: Type of error
            error_message: Error message
            
        Returns:
            bool: True if successful, False otherwise
        """
        payload = {
            "session_id": session_id,
            "error_type": error_type,
            "error_message": error_message,
            "timestamp": time.time()
        }
        
        return await self.publish_event("error_occurred", payload)
    
    async def close(self):
        """Close connections"""
        try:
            # Close RabbitMQ connection
            if self.rabbitmq_connection:
                await self.rabbitmq_connection.close()
                self.rabbitmq_connection = None
                self.rabbitmq_channel = None
            
            # Close Kafka producer
            if self.kafka_producer:
                await self.kafka_producer.stop()
                self.kafka_producer = None
            
            self.is_initialized = False
            logger.info("Event publisher closed")
        
        except Exception as e:
            logger.error(f"Error closing event publisher: {e}")


# Global event publisher instance
event_publisher = EventPublisher()