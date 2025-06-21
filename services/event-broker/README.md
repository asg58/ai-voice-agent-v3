# Event Broker Service

This service provides event brokering capabilities for the AI Voice Agent platform.

## Features

- Event publishing and consumption
- Topic-based routing
- Dead letter queues
- Event schema validation
- Batch event processing
- Priority-based event handling

## Architecture

The service follows a modular architecture with the following components:

- **API Layer**: REST API endpoints for event publishing
- **RabbitMQ Client**: Connection management for RabbitMQ
- **Event Handler**: Event processing and routing
- **Consumer Worker**: Background thread for event consumption

## Directory Structure

```
services/event-broker/
  ├── app/                      # Application code
  │   ├── main.py               # Main application entry point
  │   ├── api/                  # API endpoints
  │   │   ├── health.py         # Health check endpoints
  │   │   └── events.py         # Event management endpoints
  │   ├── core/                 # Core functionality
  │   │   ├── config.py         # Configuration
  │   │   └── rabbitmq.py       # RabbitMQ client
  │   ├── handlers/             # Event handlers
  │   │   └── event_handler.py  # Event processing
  │   └── models/               # Data models
  │       └── event.py          # Event models
  ├── Dockerfile                # Docker configuration
  ├── requirements.txt          # Python dependencies
  └── .env.example              # Example environment variables
```

## Setup

1. Create a virtual environment:

   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:

   ```
   pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env` and configure environment variables.

4. Run the service:

   ```
   uvicorn app.main:app --reload
   ```

## API Documentation

When the service is running, API documentation is available at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Events

- `POST /api/v1/events`: Publish a new event
- `POST /api/v1/events/batch`: Publish a batch of events
- `GET /api/v1/events/queues`: Get predefined queues
- `GET /api/v1/events/types`: Get event types
- `GET /api/v1/events/stats`: Get queue statistics

### Health

- `GET /health`: Get service health
- `GET /health/live`: Liveness probe
- `GET /health/ready`: Readiness probe
- `GET /health/rabbitmq`: Get RabbitMQ status

## Event Types

The service supports the following event types:

- `voice`: Voice-related events (speech recognition, TTS, etc.)
- `user`: User-related events (login, profile update, etc.)
- `system`: System-related events (service start/stop, errors, etc.)
- `notification`: Notification events (alerts, reminders, etc.)
- `custom`: Custom event types

## Docker

Build the Docker image:

```
docker build -t event-broker .
```

Run the container:

```
docker run -p 8000:8000 --env-file .env event-broker
```

## Environment Variables

| Variable                | Description                      | Default         |
| ----------------------- | -------------------------------- | --------------- |
| `HOST`                  | Host to bind to                  | `0.0.0.0`       |
| `PORT`                  | Port to bind to                  | `8000`          |
| `LOG_LEVEL`             | Logging level                    | `INFO`          |
| `RABBITMQ_HOST`         | RabbitMQ host                    | `rabbitmq`      |
| `RABBITMQ_PORT`         | RabbitMQ port                    | `5672`          |
| `RABBITMQ_USER`         | RabbitMQ username                | `guest`         |
| `RABBITMQ_PASSWORD`     | RabbitMQ password                | `guest`         |
| `RABBITMQ_VHOST`        | RabbitMQ virtual host            | `/`             |
| `DEFAULT_EXCHANGE`      | Default exchange name            | `events`        |
| `DEFAULT_EXCHANGE_TYPE` | Default exchange type            | `topic`         |
| `QUEUE_TTL`             | Queue TTL in milliseconds        | `86400000`      |
| `QUEUE_MAX_LENGTH`      | Maximum queue length             | `10000`         |
| `WORKER_PREFETCH_COUNT` | Worker prefetch count            | `10`            |
| `WORKER_POOL_SIZE`      | Worker pool size                 | `5`             |
| `SERVICE_DISCOVERY_URL` | Service discovery URL            | `service-discovery:8000` |