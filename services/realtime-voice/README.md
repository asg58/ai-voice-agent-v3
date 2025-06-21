# Real-time Voice AI Service

This service provides real-time voice processing capabilities for the AI Voice Agent platform.

## Features

- Real-time speech-to-text transcription
- Text-to-speech synthesis
- Voice activity detection
- Emotion recognition
- Voice verification
- Translation
- WebSocket communication for real-time audio streaming

## Architecture

The service follows a modular architecture with the following components:

- **API Layer**: REST API endpoints for service interaction
- **WebSocket Layer**: Real-time communication with clients
- **Audio Processing Pipeline**: Processes audio data and generates responses
- **Session Management**: Manages conversation sessions and state
- **Memory System**: Stores conversation history and context
- **Event System**: Publishes events to other services

## Directory Structure

```
services/realtime-voice/
  ├── app/                      # Application code
  │   ├── main.py               # Main application entry point
  │   ├── api/                  # API endpoints
  │   │   ├── health.py         # Health check endpoints
  │   │   ├── sessions.py       # Session management endpoints
  │   │   ├── audio.py          # Audio processing endpoints
  │   │   └── websocket.py      # WebSocket handlers
  │   ├── core/                 # Core functionality
  │   │   ├── config.py         # Configuration
  │   │   ├── audio/            # Audio processing
  │   │   ├── memory/           # Memory management
  │   │   ├── events/           # Event handling
  │   │   ├── session/          # Session management
  │   │   └── translation/      # Translation services
  │   ├── models/               # Data models
  │   │   └── models.py         # Pydantic models
  │   ├── services/             # Business logic
  │   │   └── initialization.py # Component initialization
  │   └── utils/                # Utility functions
  ├── static/                   # Static files
  ├── templates/                # HTML templates
  ├── tests/                    # Tests
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

## WebSocket API

Connect to the WebSocket endpoint at `/ws/{session_id}` to establish a real-time audio connection.

### Message Types

#### Client to Server:
- **Text Messages**: JSON messages with `type` field
  - `text_message`: Send text input
  - `ping`: Check connection
- **Binary Messages**: Raw audio data

#### Server to Client:
- **Text Messages**: JSON responses
  - `connection_established`: Connection confirmation
  - `transcription`: Speech-to-text result
  - `text_response`: Text response
  - `audio_response`: Audio response metadata
  - `error`: Error information
  - `pong`: Ping response
- **Binary Messages**: Audio data

## Docker

Build the Docker image:
```
docker build -t realtime-voice .
```

Run the container:
```
docker run -p 8000:8000 --env-file .env realtime-voice
```

## Testing

Run tests:
```
pytest
```