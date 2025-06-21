# Service Discovery Service

This service provides service discovery and health monitoring for the AI Voice Agent platform.

## Features

- Service registration and deregistration
- Service health monitoring
- Service discovery
- Automatic service cleanup

## Architecture

The service follows a modular architecture with the following components:

- **API Layer**: REST API endpoints for service interaction
- **Service Registry**: In-memory registry of services
- **Health Checker**: Background worker for health monitoring

## Directory Structure

```
services/service-discovery/
  ├── app/                      # Application code
  │   ├── main.py               # Main application entry point
  │   ├── api/                  # API endpoints
  │   │   ├── health.py         # Health check endpoints
  │   │   └── services.py       # Service management endpoints
  │   ├── core/                 # Core functionality
  │   │   ├── config.py         # Configuration
  │   │   └── ...
  │   └── models/               # Data models
  │       └── service.py        # Service models
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

### Services

- `GET /services`: Get all registered services
- `GET /services/{service_id}`: Get a service by ID
- `POST /services`: Register a new service
- `PUT /services/{service_id}`: Update a service
- `DELETE /services/{service_id}`: Deregister a service
- `GET /services/{service_id}/health`: Check the health of a service

### Health

- `GET /health`: Get service health
- `GET /health/live`: Liveness probe
- `GET /health/ready`: Readiness probe
- `GET /health/services-status`: Get services status

## Docker

Build the Docker image:

```
docker build -t service-discovery .
```

Run the container:

```
docker run -p 8000:8000 --env-file .env service-discovery
```

## Environment Variables

| Variable                | Description                      | Default     |
| ----------------------- | -------------------------------- | ----------- |
| `HOST`                  | Host to bind to                  | `0.0.0.0`   |
| `PORT`                  | Port to bind to                  | `8000`      |
| `LOG_LEVEL`             | Logging level                    | `INFO`      |
| `REDIS_HOST`            | Redis host                       | `localhost` |
| `REDIS_PORT`            | Redis port                       | `6379`      |
| `REDIS_DB`              | Redis database                   | `0`         |
| `REDIS_PASSWORD`        | Redis password                   | `""`        |
| `SERVICE_TTL`           | Service time-to-live in seconds  | `60`        |
| `HEALTH_CHECK_INTERVAL` | Health check interval in seconds | `30`        |
