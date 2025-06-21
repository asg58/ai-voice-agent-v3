"""
Kafka client for the Event Streaming service.
"""
import logging
import time
import json
import threading
from typing import Dict, Any, Optional, Callable, List
from confluent_kafka import Producer, Consumer, KafkaError, KafkaException
from confluent_kafka.admin import AdminClient, NewTopic
from tenacity import retry, stop_after_attempt, wait_fixed
from ..core.config import settings
from ..models.event import Event, EventStatus

# Configure logging
logger = logging.getLogger("kafka-client")

class KafkaClient:
    """
    Client for interacting with Kafka.
    """
    def __init__(self):
        self.producer = None
        self.consumer = None
        self.admin_client = None
        self.topics = set()
        self.consumers = {}
        self.consumer_threads = {}
        self.running = False
        self.connect()
    
    @retry(stop=stop_after_attempt(settings.CONNECTION_MAX_RETRIES), wait=wait_fixed(settings.CONNECTION_RETRY_DELAY))
    def connect(self) -> bool:
        """
        Connect to Kafka.
        
        Returns:
            bool: True if connection is successful, False otherwise
        """
        try:
            # Create producer
            producer_config = {
                'bootstrap.servers': settings.KAFKA_BOOTSTRAP_SERVERS,
                'client.id': 'event-streaming-producer',
                'acks': 'all',
                'retries': 5,
                'retry.backoff.ms': 500,
                'linger.ms': 5,
                'batch.size': 16384,
                'compression.type': 'snappy'
            }
            
            self.producer = Producer(producer_config)
            
            # Create consumer
            consumer_config = {
                'bootstrap.servers': settings.KAFKA_BOOTSTRAP_SERVERS,
                'group.id': settings.KAFKA_CONSUMER_GROUP,
                'auto.offset.reset': settings.KAFKA_AUTO_OFFSET_RESET,
                'enable.auto.commit': settings.KAFKA_ENABLE_AUTO_COMMIT,
                'auto.commit.interval.ms': settings.KAFKA_AUTO_COMMIT_INTERVAL_MS,
                'session.timeout.ms': settings.KAFKA_SESSION_TIMEOUT_MS,
                'max.poll.interval.ms': settings.KAFKA_MAX_POLL_INTERVAL_MS,
                'max.poll.records': settings.KAFKA_MAX_POLL_RECORDS
            }
            
            self.consumer = Consumer(consumer_config)
            
            # Create admin client
            admin_config = {
                'bootstrap.servers': settings.KAFKA_BOOTSTRAP_SERVERS
            }
            
            self.admin_client = AdminClient(admin_config)
            
            logger.info(f"Connected to Kafka at {settings.KAFKA_BOOTSTRAP_SERVERS}")
            
            # Setup topics
            self._setup_topics()
            
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Kafka: {str(e)}")
            raise
    
    def _setup_topics(self):
        """Setup predefined topics."""
        # Get existing topics
        existing_topics = self.list_topics()
        
        # Create topics that don't exist
        for topic_name, config in settings.PREDEFINED_TOPICS.items():
            if topic_name not in existing_topics:
                self.create_topic(
                    topic_name,
                    config.get('partitions', 3),
                    config.get('replication_factor', 1),
                    config.get('config', {})
                )
    
    def list_topics(self) -> List[str]:
        """
        List all topics.
        
        Returns:
            List[str]: List of topic names
        """
        try:
            if not self.admin_client:
                self.connect()
            
            metadata = self.admin_client.list_topics(timeout=10)
            topics = list(metadata.topics.keys())
            
            # Update topics set
            self.topics = set(topics)
            
            return topics
        except Exception as e:
            logger.error(f"Failed to list topics: {str(e)}")
            return []
    
    def create_topic(
        self,
        topic_name: str,
        partitions: int = 3,
        replication_factor: int = 1,
        config: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Create a new topic.
        
        Args:
            topic_name: The name of the topic
            partitions: Number of partitions
            replication_factor: Replication factor
            config: Additional topic configuration
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self.admin_client:
                self.connect()
            
            # Create topic
            topic = NewTopic(
                topic_name,
                num_partitions=partitions,
                replication_factor=replication_factor,
                config=config or {}
            )
            
            # Create the topic
            result = self.admin_client.create_topics([topic])
            
            # Wait for the operation to complete
            for topic, future in result.items():
                try:
                    future.result()
                    logger.info(f"Created topic: {topic}")
                    self.topics.add(topic_name)
                    return True
                except Exception as e:
                    logger.error(f"Failed to create topic {topic}: {str(e)}")
                    return False
            
            return False
        except Exception as e:
            logger.error(f"Failed to create topic {topic_name}: {str(e)}")
            return False
    
    def delete_topic(self, topic_name: str) -> bool:
        """
        Delete a topic.
        
        Args:
            topic_name: The name of the topic
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self.admin_client:
                self.connect()
            
            # Delete the topic
            result = self.admin_client.delete_topics([topic_name])
            
            # Wait for the operation to complete
            for topic, future in result.items():
                try:
                    future.result()
                    logger.info(f"Deleted topic: {topic}")
                    if topic_name in self.topics:
                        self.topics.remove(topic_name)
                    return True
                except Exception as e:
                    logger.error(f"Failed to delete topic {topic}: {str(e)}")
                    return False
            
            return False
        except Exception as e:
            logger.error(f"Failed to delete topic {topic_name}: {str(e)}")
            return False
    
    def publish(
        self,
        topic: str,
        event: Event,
        key: Optional[str] = None,
        headers: Optional[List[tuple]] = None
    ) -> bool:
        """
        Publish an event to a topic.
        
        Args:
            topic: The topic to publish to
            event: The event to publish
            key: Optional message key
            headers: Optional message headers
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self.producer:
                self.connect()
            
            # Ensure the topic exists
            if topic not in self.topics:
                existing_topics = self.list_topics()
                if topic not in existing_topics:
                    # Create the topic if it doesn't exist
                    self.create_topic(topic)
            
            # Convert event to JSON
            event_dict = event.dict()
            message_value = json.dumps(event_dict).encode('utf-8')
            
            # Use event ID as key if not provided
            if key is None:
                key = event.id
            
            # Encode key
            message_key = str(key).encode('utf-8')
            
            # Publish the message
            self.producer.produce(
                topic=topic,
                key=message_key,
                value=message_value,
                headers=headers,
                callback=self._delivery_report
            )
            
            # Flush to ensure the message is sent
            self.producer.flush(timeout=10)
            
            logger.debug(f"Published event {event.id} to topic {topic}")
            return True
        except Exception as e:
            logger.error(f"Failed to publish event to topic {topic}: {str(e)}")
            return False
    
    def _delivery_report(self, err, msg):
        """
        Delivery report callback for Kafka producer.
        
        Args:
            err: Error or None
            msg: Message object
        """
        if err is not None:
            logger.error(f"Message delivery failed: {str(err)}")
        else:
            logger.debug(f"Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")
    
    def subscribe(self, topics: List[str]):
        """
        Subscribe to topics.
        
        Args:
            topics: List of topics to subscribe to
        """
        try:
            if not self.consumer:
                self.connect()
            
            # Subscribe to topics
            self.consumer.subscribe(topics)
            logger.info(f"Subscribed to topics: {', '.join(topics)}")
        except Exception as e:
            logger.error(f"Failed to subscribe to topics: {str(e)}")
    
    def consume(self, timeout: float = 1.0) -> Optional[Dict[str, Any]]:
        """
        Consume a message from subscribed topics.
        
        Args:
            timeout: Timeout in seconds
            
        Returns:
            Optional[Dict[str, Any]]: The consumed message or None
        """
        try:
            if not self.consumer:
                self.connect()
            
            # Poll for a message
            msg = self.consumer.poll(timeout=timeout)
            
            if msg is None:
                return None
            
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    # End of partition event
                    logger.debug(f"Reached end of partition {msg.topic()} [{msg.partition()}]")
                    return None
                else:
                    # Error
                    logger.error(f"Error while consuming: {msg.error()}")
                    return None
            
            # Parse message value
            try:
                value = json.loads(msg.value().decode('utf-8'))
                
                # Add Kafka metadata
                value['partition'] = msg.partition()
                value['offset'] = msg.offset()
                
                return value
            except json.JSONDecodeError:
                logger.error(f"Failed to decode message value: {msg.value()}")
                return None
        except Exception as e:
            logger.error(f"Error while consuming: {str(e)}")
            return None
    
    def start_consumer(
        self,
        topics: List[str],
        handler: Callable[[Dict[str, Any]], None],
        group_id: Optional[str] = None
    ):
        """
        Start a consumer thread for the given topics.
        
        Args:
            topics: List of topics to consume from
            handler: Handler function for consumed messages
            group_id: Optional consumer group ID
        """
        if not group_id:
            group_id = settings.KAFKA_CONSUMER_GROUP
        
        # Create a unique ID for this consumer
        consumer_id = f"{group_id}-{'-'.join(topics)}"
        
        # Check if consumer already exists
        if consumer_id in self.consumers:
            logger.warning(f"Consumer {consumer_id} already exists")
            return
        
        # Create consumer config
        consumer_config = {
            'bootstrap.servers': settings.KAFKA_BOOTSTRAP_SERVERS,
            'group.id': group_id,
            'auto.offset.reset': settings.KAFKA_AUTO_OFFSET_RESET,
            'enable.auto.commit': settings.KAFKA_ENABLE_AUTO_COMMIT,
            'auto.commit.interval.ms': settings.KAFKA_AUTO_COMMIT_INTERVAL_MS,
            'session.timeout.ms': settings.KAFKA_SESSION_TIMEOUT_MS,
            'max.poll.interval.ms': settings.KAFKA_MAX_POLL_INTERVAL_MS,
            'max.poll.records': settings.KAFKA_MAX_POLL_RECORDS
        }
        
        # Create consumer
        consumer = Consumer(consumer_config)
        
        # Subscribe to topics
        consumer.subscribe(topics)
        
        # Store consumer
        self.consumers[consumer_id] = consumer
        
        # Create and start consumer thread
        thread = threading.Thread(
            target=self._consumer_thread,
            args=(consumer_id, consumer, handler),
            daemon=True
        )
        thread.start()
        
        # Store thread
        self.consumer_threads[consumer_id] = thread
        
        logger.info(f"Started consumer {consumer_id} for topics: {', '.join(topics)}")
    
    def _consumer_thread(
        self,
        consumer_id: str,
        consumer: Consumer,
        handler: Callable[[Dict[str, Any]], None]
    ):
        """
        Consumer thread function.
        
        Args:
            consumer_id: Consumer ID
            consumer: Consumer instance
            handler: Handler function
        """
        try:
            self.running = True
            logger.info(f"Consumer thread {consumer_id} started")
            
            while self.running:
                try:
                    # Poll for a message
                    msg = consumer.poll(timeout=1.0)
                    
                    if msg is None:
                        continue
                    
                    if msg.error():
                        if msg.error().code() == KafkaError._PARTITION_EOF:
                            # End of partition event
                            logger.debug(f"Reached end of partition {msg.topic()} [{msg.partition()}]")
                            continue
                        else:
                            # Error
                            logger.error(f"Error while consuming: {msg.error()}")
                            continue
                    
                    # Parse message value
                    try:
                        value = json.loads(msg.value().decode('utf-8'))
                        
                        # Add Kafka metadata
                        value['partition'] = msg.partition()
                        value['offset'] = msg.offset()
                        
                        # Handle the message
                        handler(value)
                        
                        # Commit offset if auto-commit is disabled
                        if not settings.KAFKA_ENABLE_AUTO_COMMIT:
                            consumer.commit(asynchronous=False)
                    except json.JSONDecodeError:
                        logger.error(f"Failed to decode message value: {msg.value()}")
                        continue
                    except Exception as e:
                        logger.error(f"Error handling message: {str(e)}")
                        continue
                except KafkaException as e:
                    logger.error(f"Kafka error in consumer thread {consumer_id}: {str(e)}")
                    # Reconnect
                    time.sleep(5)
                    continue
                except Exception as e:
                    logger.error(f"Error in consumer thread {consumer_id}: {str(e)}")
                    continue
        finally:
            # Close consumer
            consumer.close()
            logger.info(f"Consumer thread {consumer_id} stopped")
            
            # Remove consumer and thread
            if consumer_id in self.consumers:
                del self.consumers[consumer_id]
            
            if consumer_id in self.consumer_threads:
                del self.consumer_threads[consumer_id]
    
    def stop_consumer(self, consumer_id: str):
        """
        Stop a consumer thread.
        
        Args:
            consumer_id: Consumer ID
        """
        if consumer_id in self.consumers:
            # Get consumer
            consumer = self.consumers[consumer_id]
            
            # Close consumer
            consumer.close()
            
            # Wait for thread to exit
            if consumer_id in self.consumer_threads:
                thread = self.consumer_threads[consumer_id]
                thread.join(timeout=5)
            
            # Remove consumer and thread
            del self.consumers[consumer_id]
            
            if consumer_id in self.consumer_threads:
                del self.consumer_threads[consumer_id]
            
            logger.info(f"Stopped consumer {consumer_id}")
    
    def stop_all_consumers(self):
        """Stop all consumer threads."""
        self.running = False
        
        # Stop all consumers
        for consumer_id in list(self.consumers.keys()):
            self.stop_consumer(consumer_id)
    
    def close(self):
        """Close all connections."""
        # Stop all consumers
        self.stop_all_consumers()
        
        # Close producer
        if self.producer:
            self.producer.flush()
        
        logger.info("Closed Kafka connections")

# Create global Kafka client
kafka_client = KafkaClient()