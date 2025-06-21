# GraphQL API Service

This service provides a GraphQL API for the AI Voice Agent Platform, allowing clients to query and mutate data using a flexible and efficient API.

## Features

- **GraphQL API**: Provides a single endpoint for querying and mutating data
- **User Management**: Create, read, update, and delete users
- **Voice Session Management**: Create, update, and end voice sessions
- **Voice Interaction Tracking**: Record and query voice interactions
- **Event Publishing**: Publish events to RabbitMQ for other services to consume
- **Database Integration**: Store data in PostgreSQL database
- **Authentication**: Secure API with JWT authentication

## Architecture

The GraphQL API service follows a modular architecture:

- **API Layer**: GraphQL schema, types, and resolvers
- **Service Layer**: Business logic and data access
- **Model Layer**: Database models and schemas
- **Core Layer**: Configuration, database connection, and utilities

## Getting Started

### Prerequisites

- Python 3.11 or higher
- PostgreSQL database
- RabbitMQ server

### Installation

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables (see `.env.example`)
4. Run the service: `uvicorn app.main:app --host 0.0.0.0 --port 8000`

### Docker

You can also run the service using Docker:

```bash
docker build -t graphql-api .
docker run -p 8000:8000 graphql-api
```

## API Documentation

The GraphQL API is available at `/graphql`. You can use the GraphiQL interface to explore the API and execute queries and mutations.

### Example Queries

```graphql
# Get all users
query {
  users {
    id
    username
    email
    isActive
  }
}

# Get a specific user
query {
  user(id: 1) {
    id
    username
    email
    voiceSessions {
      id
      sessionId
      status
    }
  }
}

# Get voice sessions for a user
query {
  voiceSessions(userId: 1) {
    id
    sessionId
    status
    language
    startTime
    endTime
    duration
  }
}
```

### Example Mutations

```graphql
# Create a new user
mutation {
  createUser(input: {
    username: "johndoe",
    email: "john@example.com",
    password: "password123"
  }) {
    user {
      id
      username
      email
    }
  }
}

# Create a voice session
mutation {
  createVoiceSession(input: {
    userId: 1,
    language: "en-US"
  }) {
    voiceSession {
      id
      sessionId
      status
    }
  }
}

# Create a voice interaction
mutation {
  createVoiceInteraction(input: {
    sessionId: 1,
    userInput: "Hello, how can you help me?",
    systemResponse: "I can help you with various tasks. What do you need assistance with?"
  }) {
    voiceInteraction {
      id
      timestamp
      userInput
      systemResponse
    }
  }
}
```

## Integration with Other Services

The GraphQL API service integrates with other services in the AI Voice Agent Platform:

- **Service Discovery**: Registers itself with the Service Discovery service
- **Event Broker**: Publishes events to RabbitMQ for other services to consume
- **Realtime Voice Service**: Provides data for voice sessions and interactions
- **Dashboard Service**: Provides data for the dashboard UI

## Development

### Project Structure

```
graphql-api/
├── app/
│   ├── api/
│   │   ├── mutations.py
│   │   ├── schema.py
│   │   └── types.py
│   ├── core/
│   │   ├── config.py
│   │   └── database.py
│   ├── models/
│   │   ├── user.py
│   │   └── voice_session.py
│   ├── services/
│   │   ├── event_service.py
│   │   ├── user_service.py
│   │   └── voice_service.py
│   └── main.py
├── .env
├── Dockerfile
├── README.md
└── requirements.txt
```

### Testing

Run tests using pytest:

```bash
pytest
```

### Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -am 'Add my feature'`
4. Push to the branch: `git push origin feature/my-feature`
5. Submit a pull request