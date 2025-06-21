"""
WebSocket Routes for Real-time Voice Communication

WebSocket endpoints for real-time voice streaming and processing.
"""

import asyncio
import logging
import uuid
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request
from typing import Dict, Any

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/voice")
async def websocket_voice_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time voice communication.

    This endpoint handles:
    - Real-time audio streaming
    - Speech-to-text processing
    - AI conversation
    - Text-to-speech synthesis
    """
    client_id = str(uuid.uuid4())

    # Get managers from app state
    websocket_manager = getattr(websocket.app.state, 'websocket_manager', None)
    voice_processor = getattr(websocket.app.state, 'voice_processor', None)

    if not websocket_manager or not voice_processor:
        await websocket.close(code=1011, reason="Service not available")
        return

    # Connect client
    connected = await websocket_manager.connect(websocket, client_id)
    if not connected:
        return

    try:
        # Start heartbeat task
        heartbeat_task = asyncio.create_task(
            _heartbeat_loop(websocket_manager, client_id)
        )

        # Message handling loop
        while True:
            try:
                # Receive message
                message = await websocket.receive_text()

                # Handle message
                await websocket_manager.handle_message(
                    client_id, message, voice_processor
                )

            except WebSocketDisconnect:
                logger.info(f"WebSocket client {client_id} disconnected")
                break
            except Exception as e:
                logger.error(f"Error in WebSocket message loop for {client_id}: {e}")
                await websocket_manager.send_message(client_id, {
                    "type": "error",
                    "message": "Internal server error"
                })
                break

    finally:
        # Cleanup
        heartbeat_task.cancel()
        await websocket_manager.disconnect(client_id)


@router.websocket("/voice/{session_id}")
async def websocket_voice_session_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for voice communication with session management.

    Args:
        websocket: WebSocket connection
        session_id: Session identifier for conversation context
    """
    client_id = f"{session_id}_{uuid.uuid4().hex[:8]}"

    # Get managers from app state
    websocket_manager = getattr(websocket.app.state, 'websocket_manager', None)
    voice_processor = getattr(websocket.app.state, 'voice_processor', None)

    if not websocket_manager or not voice_processor:
        await websocket.close(code=1011, reason="Service not available")
        return

    # Connect client
    connected = await websocket_manager.connect(websocket, client_id)
    if not connected:
        return

    try:
        # Send session information
        await websocket_manager.send_message(client_id, {
            "type": "session",
            "session_id": session_id,
            "client_id": client_id,
            "status": "connected"
        })

        # Start heartbeat task
        heartbeat_task = asyncio.create_task(
            _heartbeat_loop(websocket_manager, client_id)
        )

        # Message handling loop
        while True:
            try:
                # Receive message
                message = await websocket.receive_text()

                # Handle message with session context
                await websocket_manager.handle_message(
                    client_id, message, voice_processor
                )

            except WebSocketDisconnect:
                logger.info(f"WebSocket session client {client_id} disconnected")
                break
            except Exception as e:
                logger.error(f"Error in WebSocket session loop for {client_id}: {e}")
                await websocket_manager.send_message(client_id, {
                    "type": "error",
                    "message": "Internal server error"
                })
                break

    finally:
        # Cleanup
        heartbeat_task.cancel()
        await websocket_manager.disconnect(client_id)


async def _heartbeat_loop(websocket_manager, client_id: str):
    """
    Heartbeat loop to keep connection alive and detect disconnections.

    Args:
        websocket_manager: WebSocket manager instance
        client_id: Client identifier
    """
    try:
        while True:
            # Wait for heartbeat interval
            await asyncio.sleep(30)  # 30 seconds

            # Send heartbeat
            success = await websocket_manager.send_message(client_id, {
                "type": "heartbeat",
                "timestamp": asyncio.get_event_loop().time()
            })

            if not success:
                logger.info(f"Heartbeat failed for client {client_id}, stopping heartbeat")
                break

    except asyncio.CancelledError:
        logger.debug(f"Heartbeat cancelled for client {client_id}")
    except Exception as e:
        logger.error(f"Error in heartbeat loop for {client_id}: {e}")


@router.get("/connections")
async def get_active_connections(request: Request) -> Dict[str, Any]:
    """
    Get information about active WebSocket connections.

    Args:
        request: FastAPI request object

    Returns:
        Dict containing connection information
    """
    try:
        websocket_manager = getattr(request.app.state, 'websocket_manager', None)
        if not websocket_manager:
            return {"error": "WebSocket manager not available"}

        status = await websocket_manager.get_status()

        return {
            "active_connections": status["connections"],
            "max_connections": status["max_connections"],
            "statistics": status["statistics"],
            "uptime_seconds": status["uptime_seconds"],
            "connection_details": status["connection_details"]
        }

    except Exception as e:
        logger.error(f"Error getting connections info: {e}")
        return {"error": str(e)}


@router.post("/broadcast")
async def broadcast_message(
    request: Request,
    message: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Broadcast message to all connected WebSocket clients.

    Args:
        request: FastAPI request object
        message: Message to broadcast

    Returns:
        Dict containing broadcast result
    """
    try:
        websocket_manager = getattr(request.app.state, 'websocket_manager', None)
        if not websocket_manager:
            return {"error": "WebSocket manager not available"}

        # Add broadcast metadata
        broadcast_message = {
            **message,
            "type": "broadcast",
            "source": "api"
        }

        # Broadcast message
        sent_count = await websocket_manager.broadcast_message(broadcast_message)

        return {
            "status": "success",
            "message_sent_to": sent_count,
            "total_connections": len(websocket_manager.active_connections)
        }

    except Exception as e:
        logger.error(f"Error broadcasting message: {e}")
        return {"error": str(e)}