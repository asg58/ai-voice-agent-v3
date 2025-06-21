# API Overview

## Endpoints

### Health Check

- **URL**: `/health`
- **Method**: `GET`
- **Description**: Returns the health status of the service.

### Session Management

- **URL**: `/sessions`
- **Method**: `POST`
- **Description**: Creates a new session.

### WebSocket Communication

- **URL**: `/ws`
- **Method**: `WebSocket`
- **Description**: Handles real-time communication.

## Authentication

- **Type**: Bearer Token
- **Header**: `Authorization: Bearer <token>`

## Error Codes

| Code | Description  |
| ---- | ------------ |
| 200  | Success      |
| 400  | Bad Request  |
| 401  | Unauthorized |
| 500  | Server Error |
