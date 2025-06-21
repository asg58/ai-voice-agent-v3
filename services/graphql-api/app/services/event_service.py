"""
Event service for GraphQL API
"""
import logging
import json
import pika
import os
from app.core.config import settings

logger = logging.getLogger(__name__)


def get_rabbitmq_connection():
    """
    Get RabbitMQ connection
    
    Returns:
        tuple: (connection, channel) or (None, None) if connection fails
    """
    try:
        credentials = pika.PlainCredentials(
            username=settings.RABBITMQ_USER,
            password=settings.RABBITMQ_PASSWORD
        )
        
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=settings.RABBITMQ_HOST,
                port=settings.RABBITMQ_PORT,
                credentials=credentials
            )
        )
        channel = connection.channel()
        
        # Declare the exchange
        channel.exchange_declare(
            exchange='graphql_events',
            exchange_type='topic',
            durable=True
        )
        
        return connection, channel
    except Exception as e:
        logger.error(f"Failed to connect to RabbitMQ: {str(e)}")
        return None, None


def publish_event(event_type, payload):
    """
    Publish an event to RabbitMQ
    
    Args:
        event_type (str): Event type
        payload (dict): Event payload
    
    Returns:
        bool: True if successful, False otherwise
    """
    connection, channel = get_rabbitmq_connection()
    
    if not connection or not channel:
        logger.warning(f"Cannot publish event {event_type}: RabbitMQ connection failed")
        return False
    
    try:
        # Add event type to payload
        message = {
            "type": event_type,
            "service": "graphql-api",
            "payload": payload
        }
        
        # Publish message
        channel.basic_publish(
            exchange='graphql_events',
            routing_key=event_type,
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2,  # make message persistent
                content_type='application/json'
            )
        )
        
        logger.info(f"Published event: {event_type}")
        connection.close()
        return True
    except Exception as e:
        logger.error(f"Failed to publish event {event_type}: {str(e)}")
        if connection and not connection.is_closed:
            connection.close()
        return False