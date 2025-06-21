from flask import Flask, jsonify
from flask_graphql import GraphQLView
from schema import schema
import logging
import os
import pika
import json
import time

# Configureer logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('graphql-api')

# RabbitMQ verbinding
def get_rabbitmq_connection():
    rabbitmq_host = os.environ.get('RABBITMQ_HOST', 'rabbitmq')
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host))
        channel = connection.channel()
        # Declareer de benodigde queues
        channel.queue_declare(queue='graphql_events')
        return connection, channel
    except Exception as e:
        logger.error(f"Kan geen verbinding maken met RabbitMQ: {str(e)}")
        return None, None

# Wacht even zodat RabbitMQ tijd heeft om op te starten
logger.info("Wachten op RabbitMQ server...")
time.sleep(5)

# Probeer verbinding te maken met RabbitMQ
rabbitmq_connection, rabbitmq_channel = get_rabbitmq_connection()
if rabbitmq_connection:
    logger.info("Verbonden met RabbitMQ")
    # Stuur een startup bericht
    try:
        rabbitmq_channel.basic_publish(
            exchange='',
            routing_key='graphql_events',
            body=json.dumps({"type": "startup", "service": "graphql-api"})
        )
        logger.info("Startup bericht verzonden naar RabbitMQ")
    except Exception as e:
        logger.error(f"Fout bij verzenden van bericht: {str(e)}")
else:
    logger.warning("Geen verbinding met RabbitMQ, events worden niet verzonden")

app = Flask(__name__)

# GraphQL endpoint
app.add_url_rule('/graphql', view_func=GraphQLView.as_view('graphql', schema=schema, graphiql=True))

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    # Controleer RabbitMQ verbinding
    rabbitmq_status = "connected" if rabbitmq_connection and not rabbitmq_connection.is_closed else "disconnected"
    
    return jsonify({
        "status": "healthy", 
        "service": "graphql-api",
        "rabbitmq": rabbitmq_status
    })

# Root endpoint
@app.route('/', methods=['GET'])
def root():
    return jsonify({
        "service": "GraphQL API",
        "endpoints": {
            "graphql": "/graphql",
            "health": "/health"
        }
    })

if __name__ == '__main__':
    logger.info("Starting GraphQL API server on port 4000")
    app.run(host='0.0.0.0', port=4000)
