"""
WebSocket Manager for Real-time Voice Communication

Manages WebSocket connections for real-time voice streaming and processing.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Set
from fastapi import WebSocket, WebSocketDisconnect
import httpx

from .config import settings

logger = logging.getLogger(__name__)


class WebSocketManager:
    """
    WebSocket Manager handles real-time voice communication.
    """

    def __init__(self):
        """Initialize the WebSocket Manager."""
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}
        self.start_time = datetime.utcnow()

        # Statistics
        self.stats = {
            "total_connections": 0,
            "active_connections": 0,
            "messages_sent": 0,
            "messages_received": 0,
            "errors": 0
        }

    async def connect(self, websocket: WebSocket, client_id: str) -> bool:
        """
        Connect a new WebSocket client.

        Args:
            websocket: WebSocket connection
            client_id: Unique client identifier

        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Check connection limit
            if len(self.active_connections) >= settings.MAX_CONNECTIONS:
                await websocket.close(code=1008, reason="Connection limit reached")
                return False

            # Accept connection
            await websocket.accept()

            # Store connection
            self.active_connections[client_id] = websocket
            self.connection_metadata[client_id] = {
                "connected_at": datetime.utcnow(),
                "last_activity": datetime.utcnow(),
                "message_count": 0
            }

            # Update statistics
            self.stats["total_connections"] += 1
            self.stats["active_connections"] = len(self.active_connections)

            logger.info(f"WebSocket client connected: {client_id}")

            # Send welcome message
            await self.send_message(client_id, {
                "type": "connection",
                "status": "connected",
                "client_id": client_id,
                "timestamp": datetime.utcnow().isoformat()
            })

            return True

        except Exception as e:
            logger.error(f"Error connecting WebSocket client {client_id}: {e}")
            self.stats["errors"] += 1
            return False

    async def disconnect(self, client_id: str) -> None:
        """
        Disconnect a WebSocket client.

        Args:
            client_id: Client identifier
        """
        try:
            # Remove connection
            if client_id in self.active_connections:
                del self.active_connections[client_id]

            if client_id in self.connection_metadata:
                del self.connection_metadata[client_id]

            # Update statistics
            self.stats["active_connections"] = len(self.active_connections)

            logger.info(f"WebSocket client disconnected: {client_id}")

        except Exception as e:
            logger.error(f"Error disconnecting WebSocket client {client_id}: {e}")
            self.stats["errors"] += 1

    async def send_message(self, client_id: str, message: Dict[str, Any]) -> bool:
        """
        Send message to a specific client.

        Args:
            client_id: Client identifier
            message: Message to send

        Returns:
            True if message sent successfully, False otherwise
        """
        try:
            if client_id not in self.active_connections:
                logger.warning(f"Client {client_id} not found")
                return False

            websocket = self.active_connections[client_id]

            # Add timestamp to message
            message["timestamp"] = datetime.utcnow().isoformat()

            # Send message
            await websocket.send_text(json.dumps(message))

            # Update metadata
            if client_id in self.connection_metadata:
                self.connection_metadata[client_id]["last_activity"] = datetime.utcnow()
                self.connection_metadata[client_id]["message_count"] += 1

            self.stats["messages_sent"] += 1
            return True

        except WebSocketDisconnect:
            logger.info(f"Client {client_id} disconnected during send")
            await self.disconnect(client_id)
            return False
        except Exception as e:
            logger.error(f"Error sending message to {client_id}: {e}")
            self.stats["errors"] += 1
            return False

    async def broadcast_message(self, message: Dict[str, Any], exclude: Optional[Set[str]] = None) -> int:
        """
        Broadcast message to all connected clients.

        Args:
            message: Message to broadcast
            exclude: Set of client IDs to exclude

        Returns:
            Number of clients message was sent to
        """
        if exclude is None:
            exclude = set()

        sent_count = 0

        # Create a copy of client IDs to avoid modification during iteration
        client_ids = list(self.active_connections.keys())

        for client_id in client_ids:
            if client_id not in exclude:
                if await self.send_message(client_id, message):
                    sent_count += 1

        return sent_count

    async def handle_message(self, client_id: str, message: str, voice_processor) -> None:
        """
        Handle incoming message from client.

        Args:
            client_id: Client identifier
            message: Received message
            voice_processor: Voice processor instance
        """
        try:
            # Parse message
            data = json.loads(message)
            message_type = data.get("type", "unknown")

            # Update statistics
            self.stats["messages_received"] += 1

            # Update activity
            if client_id in self.connection_metadata:
                self.connection_metadata[client_id]["last_activity"] = datetime.utcnow()

            logger.debug(f"Received message from {client_id}: {message_type}")

            # Handle different message types
            if message_type == "ping":
                await self.send_message(client_id, {
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                })

            elif message_type == "message":
                # Handle text message - send to core engine for AI response
                text = data.get("text", "")
                if text:
                    ai_response = await self._get_ai_response(text)
                    await self.send_message(client_id, {
                        "type": "response",
                        "text": ai_response,
                        "original_message": text
                    })

            elif message_type == "audio":
                # Handle audio data
                audio_data = data.get("data", "")
                if audio_data and voice_processor:
                    # Process audio (implement base64 decoding if needed)
                    await self.send_message(client_id, {
                        "type": "transcript",
                        "text": "Audio processing not implemented in WebSocket yet"
                    })

            elif message_type == "subscribe":
                # Handle subscription to specific events
                events = data.get("events", [])
                logger.info(f"Client {client_id} subscribed to events: {events}")

            else:
                logger.warning(f"Unknown message type from {client_id}: {message_type}")
                await self.send_message(client_id, {
                    "type": "error",
                    "message": f"Unknown message type: {message_type}"
                })

        except json.JSONDecodeError:
            logger.error(f"Invalid JSON from client {client_id}: {message}")
            await self.send_message(client_id, {
                "type": "error",
                "message": "Invalid JSON format"
            })
            self.stats["errors"] += 1

        except Exception as e:
            logger.error(f"Error handling message from {client_id}: {e}")
            await self.send_message(client_id, {
                "type": "error",
                "message": "Internal server error"
            })
            self.stats["errors"] += 1

    async def _get_ai_response(self, text: str) -> str:
        """
        Get AI response from core engine.

        Args:
            text: Input text

        Returns:
            AI response text
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{settings.CORE_ENGINE_URL}/api/v1/conversation/start",
                    json={
                        "message": text,
                        "context": {"source": "voice_websocket"}
                    },
                    timeout=10.0
                )

                if response.status_code == 200:
                    result = response.json()
                    return result.get("response", "Sorry, I couldn't process that.")
                else:
                    logger.error(f"Core engine error: {response.status_code}")
                    return "Sorry, I'm having trouble connecting to the AI service."

        except Exception as e:
            logger.error(f"Error getting AI response: {e}")
            return "Sorry, I'm having trouble processing your request."

    async def cleanup_inactive_connections(self) -> int:
        """
        Clean up inactive connections.

        Returns:
            Number of connections cleaned up
        """
        cleaned_count = 0
        current_time = datetime.utcnow()

        # Find inactive connections
        inactive_clients = []
        for client_id, metadata in self.connection_metadata.items():
            last_activity = metadata["last_activity"]
            inactive_duration = (current_time - last_activity).total_seconds()

            if inactive_duration > settings.HEARTBEAT_INTERVAL * 3:  # 3x heartbeat interval
                inactive_clients.append(client_id)

        # Disconnect inactive clients
        for client_id in inactive_clients:
            try:
                if client_id in self.active_connections:
                    await self.active_connections[client_id].close(code=1001, reason="Inactive connection")
                await self.disconnect(client_id)
                cleaned_count += 1
            except Exception as e:
                logger.error(f"Error cleaning up connection {client_id}: {e}")

        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} inactive connections")

        return cleaned_count

    async def get_status(self) -> Dict[str, Any]:
        """Get WebSocket manager status."""
        uptime = datetime.utcnow() - self.start_time

        # Get connection details
        connections_info = []
        for client_id, metadata in self.connection_metadata.items():
            connections_info.append({
                "client_id": client_id,
                "connected_at": metadata["connected_at"].isoformat(),
                "last_activity": metadata["last_activity"].isoformat(),
                "message_count": metadata["message_count"]
            })

        return {
            "uptime_seconds": uptime.total_seconds(),
            "connections": len(self.active_connections),
            "max_connections": settings.MAX_CONNECTIONS,
            "statistics": self.stats,
            "connection_details": connections_info,
            "status": "healthy"
        }

    async def cleanup(self) -> None:
        """Clean up all connections and resources."""
        logger.info("Cleaning up WebSocket Manager...")

        # Close all connections
        for client_id, websocket in list(self.active_connections.items()):
            try:
                await websocket.close(code=1001, reason="Server shutdown")
            except Exception as e:
                logger.error(f"Error closing connection {client_id}: {e}")

        # Clear all data
        self.active_connections.clear()
        self.connection_metadata.clear()
        self.stats["active_connections"] = 0

        logger.info("WebSocket Manager cleanup completed")