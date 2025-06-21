"""
RabbitMQ client for the Event Broker service.
"""
import logging
import time
import json
import pika
from typing import Dict, Any, Optional, Callable, List
from pika.adapters.blocking_connection import BlockingChannel
from pika.spec import Basic, BasicProperties
from tenacity import retry, stop_after_attempt, wait_fixed
from ..core.config import settings

# Configure logging
logger = logging.getLogger("rabbitmq-client")

class RabbitMQClient:
    """
    Client for interacting with RabbitMQ.
    """
    def __init__(self):
        self.connection = None
        self.channel = None
        self.exchanges = set()
        self.queues = set()
        self.bindings = set()
        self.consumers = {}
        self.connect()
    
    @retry(stop=stop_after_attempt(settings.CONNECTION_MAX_RETRIES), wait=wait_fixed(settings.CONNECTION_RETRY_DELAY))
    def connect(self) -> bool:
        """
        Connect to RabbitMQ server.
        
        Returns:
            bool: True if connection is successful, False otherwise
        """
        try:
            # Close existing connection if any
            if self.connection and self.connection.is_open:
                self.connection.close()
            
            # Create connection parameters
            credentials = pika.PlainCredentials(
                settings.RABBITMQ_USER,
                settings.RABBITMQ_PASSWORD
            )
            
            parameters = pika.ConnectionParameters(
                host=settings.RABBITMQ_HOST,
                port=settings.RABBITMQ_PORT,
                virtual_host=settings.RABBITMQ_VHOST,
                credentials=credentials,
                heartbeat=60,
                blocked_connection_timeout=300
            )
            
            # Connect to RabbitMQ
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            # Set QoS prefetch count
            self.channel.basic_qos(prefetch_count=settings.WORKER_PREFETCH_COUNT)
            
            logger.info(f"Connected to RabbitMQ at {settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}")
            
            # Setup exchanges and queues
            self._setup_exchanges()
            self._setup_queues()
            
            return True
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {str(e)}")
            raise
    
    def _setup_exchanges(self):
        """Setup default exchanges."""
        # Declare the default exchange
        self.declare_exchange(
            settings.DEFAULT_EXCHANGE,
            settings.DEFAULT_EXCHANGE_TYPE
        )
        
        # Declare the dead letter exchange
        self.declare_exchange(
            settings.DEAD_LETTER_EXCHANGE,
            "direct"
        )
    
    def _setup_queues(self):
        """Setup predefined queues."""
        for queue_name, config in settings.PREDEFINED_QUEUES.items():
            # Declare the queue
            self.declare_queue(
                queue_name,
                durable=config.get("durable", True),
                auto_delete=config.get("auto_delete", False),
                arguments={
                    "x-dead-letter-exchange": settings.DEAD_LETTER_EXCHANGE,
                    "x-dead-letter-routing-key": f"dead.{queue_name}",
                    "x-message-ttl": settings.QUEUE_TTL,
                    "x-max-length": settings.QUEUE_MAX_LENGTH
                }
            )
            
            # Bind the queue to the exchange
            self.bind_queue(
                queue_name,
                settings.DEFAULT_EXCHANGE,
                config.get("routing_key", "#")
            )
            
            # Declare the dead letter queue
            dead_letter_queue = f"dead.{queue_name}"
            self.declare_queue(
                dead_letter_queue,
                durable=True,
                auto_delete=False
            )
            
            # Bind the dead letter queue to the dead letter exchange
            self.bind_queue(
                dead_letter_queue,
                settings.DEAD_LETTER_EXCHANGE,
                f"dead.{queue_name}"
            )
    
    def declare_exchange(self, exchange_name: str, exchange_type: str) -> bool:
        """
        Declare an exchange.
        
        Args:
            exchange_name: The name of the exchange
            exchange_type: The type of the exchange (direct, fanout, topic, headers)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self.channel or self.channel.is_closed:
                self.connect()
            
            self.channel.exchange_declare(
                exchange=exchange_name,
                exchange_type=exchange_type,
                durable=True,
                auto_delete=False
            )
            
            self.exchanges.add(exchange_name)
            logger.info(f"Declared exchange: {exchange_name} ({exchange_type})")
            return True
        except Exception as e:
            logger.error(f"Failed to declare exchange {exchange_name}: {str(e)}")
            return False
    
    def declare_queue(
        self,
        queue_name: str,
        durable: bool = True,
        auto_delete: bool = False,
        arguments: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Declare a queue.
        
        Args:
            queue_name: The name of the queue
            durable: Whether the queue should survive broker restarts
            auto_delete: Whether the queue should be deleted when no longer used
            arguments: Additional arguments for the queue
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self.channel or self.channel.is_closed:
                self.connect()
            
            self.channel.queue_declare(
                queue=queue_name,
                durable=durable,
                auto_delete=auto_delete,
                arguments=arguments
            )
            
            self.queues.add(queue_name)
            logger.info(f"Declared queue: {queue_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to declare queue {queue_name}: {str(e)}")
            return False
    
    def bind_queue(self, queue_name: str, exchange_name: str, routing_key: str) -> bool:
        """
        Bind a queue to an exchange.
        
        Args:
            queue_name: The name of the queue
            exchange_name: The name of the exchange
            routing_key: The routing key
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self.channel or self.channel.is_closed:
                self.connect()
            
            self.channel.queue_bind(
                queue=queue_name,
                exchange=exchange_name,
                routing_key=routing_key
            )
            
            binding_key = f"{exchange_name}:{queue_name}:{routing_key}"
            self.bindings.add(binding_key)
            logger.info(f"Bound queue {queue_name} to exchange {exchange_name} with routing key {routing_key}")
            return True
        except Exception as e:
            logger.error(f"Failed to bind queue {queue_name} to exchange {exchange_name}: {str(e)}")
            return False
    
    def publish(
        self,
        exchange: str,
        routing_key: str,
        body: Dict[str, Any],
        properties: Optional[BasicProperties] = None,
        mandatory: bool = True
    ) -> bool:
        """
        Publish a message to an exchange.
        
        Args:
            exchange: The exchange to publish to
            routing_key: The routing key
            body: The message body
            properties: Message properties
            mandatory: Whether the message is mandatory
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self.channel or self.channel.is_closed:
                self.connect()
            
            # Ensure the exchange exists
            if exchange not in self.exchanges:
                self.declare_exchange(exchange, settings.DEFAULT_EXCHANGE_TYPE)
            
            # Convert body to JSON
            message_body = json.dumps(body).encode('utf-8')
            
            # Set default properties if not provided
            if properties is None:
                properties = pika.BasicProperties(
                    delivery_mode=2,  # Persistent
                    content_type='application/json',
                    timestamp=int(time.time())
                )
            
            # Publish the message
            self.channel.basic_publish(
                exchange=exchange,
                routing_key=routing_key,
                body=message_body,
                properties=properties,
                mandatory=mandatory
            )
            
            logger.debug(f"Published message to {exchange}:{routing_key}")
            return True
        except Exception as e:
            logger.error(f"Failed to publish message to {exchange}:{routing_key}: {str(e)}")
            return False
    
    def consume(
        self,
        queue: str,
        callback: Callable[[BlockingChannel, Basic.Deliver, BasicProperties, bytes], None],
        auto_ack: bool = False
    ) -> str:
        """
        Start consuming messages from a queue.
        
        Args:
            queue: The queue to consume from
            callback: The callback function to handle messages
            auto_ack: Whether to automatically acknowledge messages
            
        Returns:
            str: The consumer tag
        """
        try:
            if not self.channel or self.channel.is_closed:
                self.connect()
            
            # Ensure the queue exists
            if queue not in self.queues:
                self.declare_queue(queue)
            
            # Start consuming
            consumer_tag = self.channel.basic_consume(
                queue=queue,
                on_message_callback=callback,
                auto_ack=auto_ack
            )
            
            self.consumers[consumer_tag] = queue
            logger.info(f"Started consuming from queue {queue} with consumer tag {consumer_tag}")
            return consumer_tag
        except Exception as e:
            logger.error(f"Failed to start consuming from queue {queue}: {str(e)}")
            raise
    
    def acknowledge(self, delivery_tag: int) -> bool:
        """
        Acknowledge a message.
        
        Args:
            delivery_tag: The delivery tag of the message
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self.channel or self.channel.is_closed:
                self.connect()
            
            self.channel.basic_ack(delivery_tag=delivery_tag)
            return True
        except Exception as e:
            logger.error(f"Failed to acknowledge message {delivery_tag}: {str(e)}")
            return False
    
    def reject(self, delivery_tag: int, requeue: bool = False) -> bool:
        """
        Reject a message.
        
        Args:
            delivery_tag: The delivery tag of the message
            requeue: Whether to requeue the message
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self.channel or self.channel.is_closed:
                self.connect()
            
            self.channel.basic_reject(delivery_tag=delivery_tag, requeue=requeue)
            return True
        except Exception as e:
            logger.error(f"Failed to reject message {delivery_tag}: {str(e)}")
            return False
    
    def start_consuming(self):
        """Start consuming messages."""
        try:
            if not self.channel or self.channel.is_closed:
                self.connect()
            
            logger.info("Starting to consume messages")
            self.channel.start_consuming()
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received, stopping consumption")
            self.stop_consuming()
        except Exception as e:
            logger.error(f"Error while consuming messages: {str(e)}")
            self.stop_consuming()
    
    def stop_consuming(self):
        """Stop consuming messages."""
        try:
            if self.channel and self.channel.is_open:
                logger.info("Stopping message consumption")
                self.channel.stop_consuming()
        except Exception as e:
            logger.error(f"Error while stopping consumption: {str(e)}")
    
    def close(self):
        """Close the connection."""
        try:
            if self.connection and self.connection.is_open:
                logger.info("Closing RabbitMQ connection")
                self.connection.close()
        except Exception as e:
            logger.error(f"Error while closing connection: {str(e)}")

# Create global RabbitMQ client
rabbitmq_client = RabbitMQClient()