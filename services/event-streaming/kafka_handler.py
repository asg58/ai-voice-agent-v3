import os
import json
import time
import threading
import logging
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError, NoBrokersAvailable
from flask import Flask, request, jsonify

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('kafka_handler')

app = Flask(__name__)

class KafkaHandler:
    def __init__(self, broker_url, max_retries=5, retry_interval=5):
        self.broker_url = broker_url
        self.max_retries = max_retries
        self.retry_interval = retry_interval
        self.producer = None
        self.is_connected = False
        self.in_memory_messages = []  # Backup storage for messages when Kafka is unavailable
        
        # Try to connect to Kafka
        self._connect_to_kafka()
        
        # Start a background thread to retry connection if it failed
        if not self.is_connected:
            self._start_reconnect_thread()

    def _connect_to_kafka(self):
        """Attempt to connect to Kafka broker"""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.broker_url,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks='all',  # Wait for all replicas to acknowledge
                retries=3,   # Retry a few times if sending fails
                request_timeout_ms=5000  # 5 seconds timeout
            )
            # Test the connection
            self.producer.bootstrap_connected()
            self.is_connected = True
            logger.info(f"Successfully connected to Kafka broker at {self.broker_url}")
            
            # If we have cached messages, try to send them now
            if self.in_memory_messages:
                self._process_cached_messages()
                
        except (KafkaError, NoBrokersAvailable) as e:
            logger.error(f"Failed to connect to Kafka broker: {e}")
            self.is_connected = False
            self.producer = None
    
    def _start_reconnect_thread(self):
        """Start a background thread to periodically try reconnecting to Kafka"""
        def reconnect_thread():
            retries = 0
            while not self.is_connected and (retries < self.max_retries or self.max_retries <= 0):
                logger.info(f"Attempting to reconnect to Kafka broker (attempt {retries+1})")
                time.sleep(self.retry_interval)
                self._connect_to_kafka()
                retries += 1
                
            if not self.is_connected:
                logger.warning("Failed to reconnect to Kafka after maximum retries")
        
        thread = threading.Thread(target=reconnect_thread)
        thread.daemon = True
        thread.start()
    
    def _process_cached_messages(self):
        """Try to send cached messages to Kafka"""
        if not self.is_connected or not self.in_memory_messages:
            return
            
        logger.info(f"Attempting to send {len(self.in_memory_messages)} cached messages to Kafka")
        
        # Create a copy of the list to avoid modification during iteration
        cached_messages = self.in_memory_messages.copy()
        successful_indices = []
        
        for i, (topic, message) in enumerate(cached_messages):
            try:
                future = self.producer.send(topic, message)
                future.get(timeout=5)
                successful_indices.append(i)
                logger.info(f"Successfully sent cached message to topic {topic}")
            except Exception as e:
                logger.error(f"Failed to send cached message to topic {topic}: {e}")
                break  # Stop processing if we encounter an error
        
        # Remove successfully sent messages from the cache
        # We need to process in reverse order to avoid index shifting
        for i in sorted(successful_indices, reverse=True):
            del self.in_memory_messages[i]
            
        if self.in_memory_messages:
            logger.info(f"Still have {len(self.in_memory_messages)} messages in cache")
        else:
            logger.info("All cached messages have been sent to Kafka")

    def send_event(self, topic, message):
        """Send an event to Kafka or store it in memory if Kafka is unavailable"""
        # If we're connected to Kafka, try to send the message
        if self.is_connected and self.producer:
            try:
                future = self.producer.send(topic, message)
                record_metadata = future.get(timeout=10)
                logger.info(f"Message sent to topic {topic} at partition {record_metadata.partition}, offset {record_metadata.offset}")
                
                # Also store in our in-memory messages for the API
                messages.append(message)
                return True
            except Exception as e:
                logger.error(f"Error sending message to Kafka topic {topic}: {e}")
                # Fall back to in-memory storage
                self.in_memory_messages.append((topic, message))
                messages.append(message)
                return True  # We still return True since we stored the message
        else:
            # Store in memory for later sending
            logger.warning(f"Kafka not available, storing message for topic {topic} in memory")
            self.in_memory_messages.append((topic, message))
            messages.append(message)
            return True  # We still return True since we stored the message

    def consume_events(self, topic, callback):
        """Start a consumer for the given topic"""
        def consumer_thread():
            while True:
                if self.is_connected:
                    try:
                        consumer = KafkaConsumer(
                            topic,
                            bootstrap_servers=self.broker_url,
                            auto_offset_reset='latest',
                            enable_auto_commit=True,
                            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                            group_id=f'event-streaming-{topic}',  # Unique consumer group
                            session_timeout_ms=30000,  # 30 seconds
                            heartbeat_interval_ms=10000  # 10 seconds
                        )
                        
                        logger.info(f"Started consuming from topic {topic}")
                        
                        for message in consumer:
                            try:
                                logger.info(f"Received message from topic {topic}: {message.value}")
                                callback(message.value)
                            except Exception as e:
                                logger.error(f"Error processing message from topic {topic}: {e}")
                                
                    except Exception as e:
                        logger.error(f"Error in consumer thread for topic {topic}: {e}")
                        self.is_connected = False
                        time.sleep(5)  # Wait before retrying
                else:
                    logger.warning(f"Not connected to Kafka, cannot consume from topic {topic}")
                    time.sleep(5)  # Wait before checking connection again
        
        thread = threading.Thread(target=consumer_thread)
        thread.daemon = True
        thread.start()
        return thread

# Initialize Kafka handler
broker_url = os.environ.get('KAFKA_BROKER_URL', 'localhost:9092')
kafka_handler = KafkaHandler(broker_url)

# Global in-memory message store for the API
messages = []

def process_message(message):
    """Process a message received from Kafka"""
    logger.info(f"Processing message: {message}")
    messages.append(message)

# Start a consumer for the 'events' topic
kafka_handler.consume_events('events', process_message)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

@app.route('/send', methods=['POST'])
def send_event():
    data = request.json
    if not data or 'topic' not in data or 'message' not in data:
        return jsonify({"error": "Missing required fields: topic, message"}), 400
    
    success = kafka_handler.send_event(data['topic'], data['message'])
    if success:
        return jsonify({"status": "success"}), 200
    else:
        return jsonify({"status": "error", "message": "Failed to send event"}), 500

@app.route('/messages', methods=['GET'])
def get_messages():
    return jsonify({"messages": messages}), 200

if __name__ == '__main__':
    print("Starting Event Streaming Service...")
    port = int(os.environ.get('PORT', 9092))
    app.run(host='0.0.0.0', port=port, debug=False)