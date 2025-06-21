"""
Enhanced WebSocket Manager with Connection Pooling and Health Monitoring
Supports horizontal scaling and high-performance real-time communication
"""
import asyncio
import time
import json
import logging
from typing import Dict, Set, Any, Optional
from collections import defaultdict
from dataclasses import dataclass, field
from fastapi import WebSocket, WebSocketDisconnect
import redis.asyncio as redis

logger = logging.getLogger(__name__)

@dataclass
class WebSocketConnection:
    websocket: WebSocket
    session_id: str
    user_id: str
    created_at: float
    last_activity: float
    message_count: int = 0
    bytes_sent: int = 0
    bytes_received: int = 0
    errors: int = 0
    tags: Set[str] = field(default_factory=set)

class EnhancedWebSocketManager:
    """
    High-performance WebSocket manager with:
    - Connection pooling and health monitoring
    - Message broadcasting and routing
    - Automatic cleanup and error handling
    - Redis-based scaling support
    """
    
    def __init__(self, redis_url: str = None, max_connections: int = 1000):
        self.connections: Dict[str, WebSocketConnection] = {}
        self.user_sessions: Dict[str, Set[str]] = defaultdict(set)
        self.session_tags: Dict[str, Set[str]] = defaultdict(set)
        
        # Connection limits and cleanup
        self.max_connections = max_connections
        self.cleanup_interval = 60  # seconds
        self.inactive_timeout = 300  # 5 minutes
        
        # Redis for distributed scaling
        self.redis_client = None
        if redis_url:
            self.redis_client = redis.from_url(redis_url)
            
        # Performance metrics
        self.stats = {
            "total_connections": 0,
            "messages_sent": 0,
            "messages_received": 0,
            "bytes_transferred": 0,
            "errors": 0,
            "cleanup_runs": 0
        }
        
        # Background tasks
        self.cleanup_task = None
        self.heartbeat_task = None
        
    async def start(self):
        """Start background management tasks"""
        self.cleanup_task = asyncio.create_task(self._cleanup_worker())
        self.heartbeat_task = asyncio.create_task(self._heartbeat_worker())
        logger.info("WebSocket manager started")
        
    async def stop(self):
        """Stop manager and close all connections"""
        # Cancel background tasks
        if self.cleanup_task:
            self.cleanup_task.cancel()
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
            
        # Close all connections gracefully
        close_tasks = []
        for session_id in list(self.connections.keys()):
            task = asyncio.create_task(
                self.disconnect(session_id, reason="Server shutdown")
            )
            close_tasks.append(task)
            
        if close_tasks:
            await asyncio.gather(*close_tasks, return_exceptions=True)
            
        # Close Redis connection
        if self.redis_client:
            await self.redis_client.close()
            
        logger.info("WebSocket manager stopped")
        
    async def connect(self, websocket: WebSocket, session_id: str, user_id: str, tags: Set[str] = None) -> bool:
        """
        Accept new WebSocket connection with enhanced tracking
        """
        try:
            # Check connection limits
            if len(self.connections) >= self.max_connections:
                await self._evict_oldest_connection()
                
            # Accept connection
            await websocket.accept()
            
            # Create connection object
            connection = WebSocketConnection(
                websocket=websocket,
                session_id=session_id,
                user_id=user_id,
                created_at=time.time(),
                last_activity=time.time(),
                tags=tags or set()
            )
            
            # Store connection
            self.connections[session_id] = connection
            self.user_sessions[user_id].add(session_id)
            
            if tags:
                for tag in tags:
                    self.session_tags[tag].add(session_id)
                    
            # Update stats
            self.stats["total_connections"] += 1
            
            # Notify other instances via Redis
            if self.redis_client:
                await self._publish_connection_event("connect", session_id, user_id)
                
            logger.info(f"WebSocket connected: session={session_id}, user={user_id}")
            
            # Send welcome message
            await self.send_to_session(session_id, {
                "type": "connection_established",
                "session_id": session_id,
                "user_id": user_id,
                "server_time": time.time(),
                "features": ["real_time_audio", "text_messaging", "file_upload"]
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to accept WebSocket connection: {e}")
            return False
            
    async def disconnect(self, session_id: str, reason: str = "Normal closure"):
        """Gracefully disconnect WebSocket"""
        if session_id not in self.connections:
            return
            
        connection = self.connections[session_id]
        
        try:
            # Send goodbye message
            await connection.websocket.send_json({
                "type": "connection_closing",
                "reason": reason,
                "session_stats": {
                    "duration": time.time() - connection.created_at,
                    "messages": connection.message_count,
                    "bytes_sent": connection.bytes_sent,
                    "bytes_received": connection.bytes_received
                }
            })
            
            # Close WebSocket
            await connection.websocket.close()
            
        except Exception as e:
            logger.debug(f"Error during disconnect: {e}")
            
        finally:
            # Clean up tracking
            self._remove_connection(session_id)
            
            # Notify other instances
            if self.redis_client:
                await self._publish_connection_event("disconnect", session_id, connection.user_id)
                
            logger.info(f"WebSocket disconnected: session={session_id}")
            
    async def send_to_session(self, session_id: str, message: Dict[str, Any]) -> bool:
        """Send message to specific session"""
        if session_id not in self.connections:
            return False
            
        connection = self.connections[session_id]
        
        try:
            # Add metadata
            message["timestamp"] = time.time()
            message["server_id"] = "voice-ai-1"  # Could be dynamic
            
            # Send message
            if isinstance(message, dict):
                message_str = json.dumps(message)
                await connection.websocket.send_text(message_str)
                connection.bytes_sent += len(message_str.encode())
            else:
                await connection.websocket.send_bytes(message)
                connection.bytes_sent += len(message)
                
            # Update tracking
            connection.message_count += 1
            connection.last_activity = time.time()
            self.stats["messages_sent"] += 1
            
            return True
            
        except WebSocketDisconnect:
            await self.disconnect(session_id, "Client disconnected")
            return False
        except Exception as e:
            connection.errors += 1
            self.stats["errors"] += 1
            logger.error(f"Error sending to session {session_id}: {e}")
            return False
            
    async def send_to_user(self, user_id: str, message: Dict[str, Any]) -> int:
        """Send message to all sessions of a user"""
        session_ids = self.user_sessions.get(user_id, set())
        sent_count = 0
        
        for session_id in list(session_ids):  # Copy to avoid modification during iteration
            if await self.send_to_session(session_id, message):
                sent_count += 1
                
        return sent_count
        
    async def broadcast_to_tag(self, tag: str, message: Dict[str, Any]) -> int:
        """Broadcast message to all sessions with specific tag"""
        session_ids = self.session_tags.get(tag, set())
        sent_count = 0
        
        tasks = []
        for session_id in list(session_ids):
            task = asyncio.create_task(self.send_to_session(session_id, message))
            tasks.append(task)
            
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            sent_count = sum(1 for result in results if result is True)
            
        return sent_count
        
    async def broadcast_to_all(self, message: Dict[str, Any]) -> int:
        """Broadcast message to all connected sessions"""
        session_ids = list(self.connections.keys())
        sent_count = 0
        
        # Send in batches to avoid overwhelming
        batch_size = 50
        for i in range(0, len(session_ids), batch_size):
            batch = session_ids[i:i + batch_size]
            tasks = [
                asyncio.create_task(self.send_to_session(session_id, message))
                for session_id in batch
            ]
            
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                sent_count += sum(1 for result in results if result is True)
                
        return sent_count
        
    async def receive_from_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Receive message from specific session"""
        if session_id not in self.connections:
            return None
            
        connection = self.connections[session_id]
        
        try:
            # Receive with timeout
            message = await asyncio.wait_for(
                connection.websocket.receive(),
                timeout=30.0
            )
            
            # Update tracking
            connection.last_activity = time.time()
            self.stats["messages_received"] += 1
            
            # Process message
            if "text" in message:
                data = json.loads(message["text"])
                connection.bytes_received += len(message["text"].encode())
                return data
            elif "bytes" in message:
                connection.bytes_received += len(message["bytes"])
                return {"type": "binary", "data": message["bytes"]}
                
        except asyncio.TimeoutError:
            logger.debug(f"Receive timeout for session {session_id}")
        except WebSocketDisconnect:
            await self.disconnect(session_id, "Client disconnected")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON from session {session_id}: {e}")
            connection.errors += 1
        except Exception as e:
            logger.error(f"Error receiving from session {session_id}: {e}")
            connection.errors += 1
            
        return None
        
    def get_connection_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed connection information"""
        if session_id not in self.connections:
            return None
            
        connection = self.connections[session_id]
        
        return {
            "session_id": session_id,
            "user_id": connection.user_id,
            "created_at": connection.created_at,
            "last_activity": connection.last_activity,
            "duration": time.time() - connection.created_at,
            "message_count": connection.message_count,
            "bytes_sent": connection.bytes_sent,
            "bytes_received": connection.bytes_received,
            "errors": connection.errors,
            "tags": list(connection.tags),
            "status": "active" if time.time() - connection.last_activity < 30 else "idle"
        }
        
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive WebSocket statistics"""
        current_time = time.time()
        
        # Calculate connection stats
        active_connections = sum(
            1 for conn in self.connections.values()
            if current_time - conn.last_activity < 30
        )
        
        idle_connections = len(self.connections) - active_connections
        
        # Calculate traffic stats
        total_bytes = sum(
            conn.bytes_sent + conn.bytes_received
            for conn in self.connections.values()
        )
        
        return {
            "connections": {
                "total": len(self.connections),
                "active": active_connections,
                "idle": idle_connections,
                "max_allowed": self.max_connections
            },
            "traffic": {
                "total_messages_sent": self.stats["messages_sent"],
                "total_messages_received": self.stats["messages_received"],
                "total_bytes_transferred": total_bytes,
                "errors": self.stats["errors"]
            },
            "users": {
                "unique_users": len(self.user_sessions),
                "sessions_per_user": len(self.connections) / max(len(self.user_sessions), 1)
            },
            "tags": {
                "total_tags": len(self.session_tags),
                "tag_distribution": {
                    tag: len(sessions) for tag, sessions in self.session_tags.items()
                }
            },
            "performance": {
                "cleanup_runs": self.stats["cleanup_runs"],
                "uptime": current_time - self.stats.get("start_time", current_time)
            }
        }
        
    async def _cleanup_worker(self):
        """Background worker for connection cleanup"""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self._cleanup_inactive_connections()
                self.stats["cleanup_runs"] += 1
            except Exception as e:
                logger.error(f"Error in cleanup worker: {e}")
                
    async def _heartbeat_worker(self):
        """Background worker for sending heartbeat pings"""
        while True:
            try:
                await asyncio.sleep(30)  # Send ping every 30 seconds
                
                # Send ping to all active connections
                ping_message = {
                    "type": "ping",
                    "server_time": time.time()
                }
                
                await self.broadcast_to_all(ping_message)
                
            except Exception as e:
                logger.error(f"Error in heartbeat worker: {e}")
                
    async def _cleanup_inactive_connections(self):
        """Remove inactive connections"""
        current_time = time.time()
        inactive_sessions = []
        
        for session_id, connection in self.connections.items():
            if current_time - connection.last_activity > self.inactive_timeout:
                inactive_sessions.append(session_id)
                
        for session_id in inactive_sessions:
            await self.disconnect(session_id, "Inactive connection cleanup")
            
        if inactive_sessions:
            logger.info(f"Cleaned up {len(inactive_sessions)} inactive connections")
            
    async def _evict_oldest_connection(self):
        """Evict oldest connection to make room for new one"""
        if not self.connections:
            return
            
        oldest_session = min(
            self.connections.keys(),
            key=lambda sid: self.connections[sid].created_at
        )
        
        await self.disconnect(oldest_session, "Connection limit reached")
        
    def _remove_connection(self, session_id: str):
        """Remove connection from all tracking structures"""
        if session_id not in self.connections:
            return
            
        connection = self.connections[session_id]
        
        # Remove from main connections
        del self.connections[session_id]
        
        # Remove from user sessions
        self.user_sessions[connection.user_id].discard(session_id)
        if not self.user_sessions[connection.user_id]:
            del self.user_sessions[connection.user_id]
            
        # Remove from tags
        for tag in connection.tags:
            self.session_tags[tag].discard(session_id)
            if not self.session_tags[tag]:
                del self.session_tags[tag]
                
    async def accept_connection(self, websocket: WebSocket, session_id: str, user_id: str = None) -> Optional[str]:
        """Accept a new WebSocket connection and return connection ID"""
        if user_id is None:
            user_id = session_id  # Use session_id as user_id if not provided
            
        # Check connection limits
        if len(self.connections) >= self.max_connections:
            await self._evict_oldest_connection()
            
        # Accept the WebSocket connection
        await websocket.accept()
        
        # Create connection tracking
        connection_id = f"{session_id}_{int(time.time() * 1000)}"
        
        connection = WebSocketConnection(
            websocket=websocket,
            session_id=session_id,
            user_id=user_id,
            created_at=time.time(),
            last_activity=time.time()
        )
        
        self.connections[connection_id] = connection
        self.user_sessions[user_id].add(connection_id)
        
        # Publish connection event
        await self._publish_connection_event("connected", session_id, user_id)
        
        logger.info(f"WebSocket connection accepted: {connection_id}")
        return connection_id
    
    async def remove_connection(self, connection_id: str):
        """Remove a WebSocket connection"""
        if connection_id not in self.connections:
            return
            
        connection = self.connections[connection_id]
        
        # Remove from tracking
        self.user_sessions[connection.user_id].discard(connection_id)
        if not self.user_sessions[connection.user_id]:
            del self.user_sessions[connection.user_id]
            
        # Remove from tags
        for tag in connection.tags:
            self.session_tags[tag].discard(connection_id)
            if not self.session_tags[tag]:
                del self.session_tags[tag]
                
        del self.connections[connection_id]
        
        # Publish disconnection event
        await self._publish_connection_event("disconnected", connection.session_id, connection.user_id)
        
        logger.info(f"WebSocket connection removed: {connection_id}")
    
    async def handle_connection(self, connection_id: str, websocket: WebSocket, session):
        """Handle WebSocket connection with optimized message processing"""
        from src.core.audio.optimized_pipeline import optimized_pipeline
        from src.core.monitoring.advanced_metrics import voice_ai_metrics
        import json
        
        if connection_id not in self.connections:
            logger.error(f"Connection {connection_id} not found")
            return
            
        connection = self.connections[connection_id]
        
        try:
            # Process messages
            while True:
                # Receive message with timeout
                try:
                    message = await asyncio.wait_for(websocket.receive(), timeout=30.0)
                except asyncio.TimeoutError:
                    # Send heartbeat
                    await websocket.send_json({"type": "heartbeat", "timestamp": time.time()})
                    continue
                
                # Update activity
                connection.last_activity = time.time()
                connection.message_count += 1
                
                # Check message type
                if "text" in message:
                    # Process text message
                    data = json.loads(message["text"])
                    await self._process_text_message(websocket, connection, session, data)
                elif "bytes" in message:
                    # Process binary message (audio)
                    audio_data = message["bytes"]
                    connection.bytes_received += len(audio_data)
                    await self._process_audio_message(websocket, connection, session, audio_data)
                    
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected: {connection_id}")
        except Exception as e:
            logger.error(f"Error handling WebSocket connection {connection_id}: {e}")
            connection.errors += 1
            voice_ai_metrics.increment("websocket_message_errors_total")
    
    async def _process_text_message(self, websocket: WebSocket, connection: WebSocketConnection, session, data: Dict):
        """Process text message from WebSocket"""
        from src.core.audio.optimized_pipeline import optimized_pipeline
        
        message_type = data.get("type", "")
        
        if message_type == "text_input":
            # Process text input
            user_text = data.get("text", "")
            if not user_text:
                await websocket.send_json({
                    "type": "error",
                    "message": "Text input is empty"
                })
                return
            
            # Process text with optimized pipeline
            async for response_chunk in optimized_pipeline.process_text(session.session_id, user_text):
                await websocket.send_json({
                    "type": "text_response",
                    "text": response_chunk
                })
                connection.bytes_sent += len(response_chunk.encode())
        
        elif message_type == "command":
            # Process command
            command = data.get("command", "")
            if command == "reset_conversation":
                # Reset conversation
                await optimized_pipeline.reset_conversation(session.session_id)
                await websocket.send_json({
                    "type": "command_response",
                    "command": "reset_conversation",
                    "status": "success"
                })
            else:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown command: {command}"
                })
        
        else:
            await websocket.send_json({
                "type": "error",
                "message": f"Unknown message type: {message_type}"
            })
    
    async def _process_audio_message(self, websocket: WebSocket, connection: WebSocketConnection, session, audio_data: bytes):
        """Process audio message from WebSocket with optimized pipeline"""
        from src.core.audio.optimized_pipeline import optimized_pipeline
        from src.core.monitoring.advanced_metrics import voice_ai_metrics
        from config.settings import SAMPLE_RATE, CHANNELS
        from models import AudioChunk
        
        if not audio_data:
            await websocket.send_json({
                "type": "error",
                "message": "Empty audio data"
            })
            return
        
        try:
            # Create audio chunk
            chunk = AudioChunk(
                session_id=session.session_id,
                data=audio_data,
                sample_rate=SAMPLE_RATE,
                channels=CHANNELS,
                timestamp=time.time()
            )
            
            # Process audio with optimized pipeline (non-blocking)
            asyncio.create_task(
                self._handle_audio_processing(websocket, connection, session, chunk)
            )
            
        except Exception as e:
            logger.error(f"Error processing audio message: {e}")
            voice_ai_metrics.increment("audio_processing_errors_total")
            await websocket.send_json({
                "type": "error",
                "message": f"Audio processing error: {str(e)}"
            })
    
    async def _handle_audio_processing(self, websocket: WebSocket, connection: WebSocketConnection, session, chunk):
        """Handle audio processing in background task"""
        from src.core.audio.optimized_pipeline import optimized_pipeline
        
        try:
            # Process audio with optimized pipeline
            result = await optimized_pipeline.process_audio(chunk)
            
            # Send transcription result
            if result and result.text:
                response_data = {
                    "type": "transcription",
                    "text": result.text,
                    "is_final": result.is_final,
                    "language": result.language,
                    "confidence": result.confidence if hasattr(result, 'confidence') else 0.0
                }
                
                await websocket.send_json(response_data)
                connection.bytes_sent += len(str(response_data).encode())
                
                # If final result, generate response
                if result.is_final:
                    # Generate AI response asynchronously
                    asyncio.create_task(
                        self._generate_ai_response(websocket, connection, session, result)
                    )
                    
        except Exception as e:
            logger.error(f"Error in audio processing task: {e}")
            await websocket.send_json({
                "type": "error",
                "message": f"Audio processing failed: {str(e)}"
            })
    
    async def _generate_ai_response(self, websocket: WebSocket, connection: WebSocketConnection, session, transcription_result):
        """Generate AI response in background"""
        from src.core.audio.optimized_pipeline import optimized_pipeline
        
        try:
            # Generate AI response
            response = await optimized_pipeline.generate_response(session.session_id, transcription_result)
            
            # Send text response
            text_response = {
                "type": "text_response",
                "text": response.text
            }
            await websocket.send_json(text_response)
            connection.bytes_sent += len(str(text_response).encode())
            
            # Generate audio response
            audio_response = await optimized_pipeline.synthesize_speech(response)
            
            # Send audio response in chunks (non-blocking)
            asyncio.create_task(
                self._stream_audio_response(websocket, connection, audio_response)
            )
            
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            await websocket.send_json({
                "type": "error",
                "message": f"Response generation failed: {str(e)}"
            })
    
    async def _stream_audio_response(self, websocket: WebSocket, connection: WebSocketConnection, audio_response):
        """Stream audio response in chunks"""
        try:
            # Send audio response in chunks
            chunk_size = 16000  # 1 second of audio at 16kHz
            for i in range(0, len(audio_response.audio_data), chunk_size):
                chunk = audio_response.audio_data[i:i+chunk_size]
                await websocket.send_bytes(chunk)
                connection.bytes_sent += len(chunk)
                
                # Small delay to prevent flooding
                await asyncio.sleep(0.05)
            
            # Send end of audio marker
            await websocket.send_json({
                "type": "audio_end",
                "message": "Audio response complete"
            })
            
        except Exception as e:
            logger.error(f"Error streaming audio response: {e}")

    async def _publish_connection_event(self, event_type: str, session_id: str, user_id: str):
        """Publish connection events to Redis for other instances"""
        if not self.redis_client:
            return
            
        try:
            event_data = {
                "type": event_type,
                "session_id": session_id,
                "user_id": user_id,
                "timestamp": time.time(),
                "server_id": "voice-ai-1"  # Could be dynamic
            }
            
            await self.redis_client.publish(
                "websocket_events",
                json.dumps(event_data)
            )
            
        except Exception as e:
            logger.error(f"Failed to publish WebSocket event: {e}")

# Global instance
enhanced_websocket_manager = EnhancedWebSocketManager()
