"""
Real-time Conversational AI - Simplified Main Service for Phase 1 Testing
Basic version without complex audio dependencies
"""
import asyncio
import logging
import uuid
from contextlib import asynccontextmanager
from typing import Dict, Optional
import json
import time
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import uvicorn

# Simplified imports without external audio dependencies
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Simplified data models for testing
class ConversationSession:
    def __init__(self, session_id: str, user_id: Optional[str] = None):
        self.session_id = session_id
        self.user_id = user_id
        self.messages = []
        self.started_at = datetime.now()
        self.last_activity = datetime.now()
        self.status = "active"
        self.language = "nl"
    
    def add_message(self, role: str, content: str):
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        self.messages.append(message)
        self.last_activity = datetime.now()
        return message


class HealthCheckResult:
    def __init__(self, service: str, status: str):
        self.service = service
        self.status = status
        self.timestamp = datetime.now()
        self.details = {}


# Application lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle"""
    
    # Startup
    logger.info("🚀 Starting Real-time Conversational AI Service (Phase 1 Test)")
    
    try:
        # Initialize basic components (simplified for testing)
        logger.info("✅ Basic components initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize components: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Real-time Conversational AI Service")
    
    try:
        logger.info("✅ Shutdown completed successfully")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# Create FastAPI app
app = FastAPI(
    title="Real-time Conversational AI (Phase 1 Test)",
    description="Natural, human-like AI agent with real-time voice conversation - Basic testing version",
    version="1.0.0-alpha",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
active_sessions: Dict[str, ConversationSession] = {}
websocket_connections: Dict[str, WebSocket] = {}


@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "Real-time Conversational AI",
        "version": "1.0.0-alpha",
        "phase": "Phase 1 Testing",
        "status": "running",
        "features": [
            "Basic session management",
            "WebSocket communication",
            "Health monitoring",
            "Foundation for real-time voice"
        ],
        "endpoints": {
            "health": "/health",
            "sessions": "/sessions",
            "websocket": "/ws/{session_id}"
        },
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    
    # Basic component checks
    checks = {
        "api": "healthy",
        "sessions": f"{len(active_sessions)} active",
        "websockets": f"{len(websocket_connections)} connected",
        "memory": "normal"
    }
    
    health_status = {
        "service": "realtime-voice-ai",
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "details": checks,
        "uptime_seconds": time.time() - start_time
    }
    
    return health_status


@app.post("/sessions")
async def create_session(user_id: Optional[str] = None):
    """Create a new conversation session"""
    
    session_id = str(uuid.uuid4())
    
    session = ConversationSession(
        session_id=session_id,
        user_id=user_id
    )
    
    active_sessions[session_id] = session
    
    logger.info(f"📝 Created new session {session_id} for user {user_id}")
    
    return {
        "session_id": session_id,
        "status": "created",
        "language": session.language,
        "created_at": session.started_at.isoformat()
    }


@app.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Get session information"""
    
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = active_sessions[session_id]
    
    return {
        "session_id": session.session_id,
        "user_id": session.user_id,
        "status": session.status,
        "language": session.language,
        "started_at": session.started_at.isoformat(),
        "last_activity": session.last_activity.isoformat(),
        "message_count": len(session.messages),
        "messages": session.messages[-5:] if session.messages else []  # Last 5 messages
    }


@app.delete("/sessions/{session_id}")
async def end_session(session_id: str):
    """End a conversation session"""
    
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
      # Close WebSocket if connected
    if session_id in websocket_connections:
        try:
            await websocket_connections[session_id].close()
        except Exception as e:
            logger.warning(f"Error closing WebSocket for session {session_id}: {e}")
        del websocket_connections[session_id]
    
    # Remove session
    session = active_sessions[session_id]
    session.status = "ended"
    del active_sessions[session_id]
    
    logger.info(f"🔚 Ended session {session_id}")
    
    return {
        "status": "ended",
        "session_id": session_id,
        "ended_at": datetime.now().isoformat()
    }


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time communication"""
    
    await websocket.accept()
    websocket_connections[session_id] = websocket
    
    logger.info(f"🔌 WebSocket connected for session {session_id}")
    
    # Ensure session exists
    if session_id not in active_sessions:
        await websocket.send_text(json.dumps({
            "type": "error",
            "error": "Session not found",
            "session_id": session_id
        }))
        await websocket.close()
        return
    
    try:
        # Send welcome message
        welcome_msg = {
            "type": "status",
            "session_id": session_id,
            "status": "connected",
            "message": "Connected to Real-time AI (Phase 1 Test)",
            "timestamp": datetime.now().isoformat()
        }
        await websocket.send_text(json.dumps(welcome_msg))
        
        # Message handling loop
        while True:
            try:
                # Receive message
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle different message types
                await handle_websocket_message(session_id, message, websocket)
                
            except WebSocketDisconnect:
                logger.info(f"🔌 WebSocket disconnected for session {session_id}")
                break
            except json.JSONDecodeError:
                error_msg = {
                    "type": "error",
                    "session_id": session_id,
                    "error_code": "INVALID_JSON",
                    "error_message": "Invalid JSON message"
                }
                await websocket.send_text(json.dumps(error_msg))
            except Exception as e:
                logger.error(f"❌ Error handling WebSocket message: {e}")
                error_msg = {
                    "type": "error",
                    "session_id": session_id,
                    "error_code": "PROCESSING_ERROR",
                    "error_message": str(e)
                }
                await websocket.send_text(json.dumps(error_msg))
    
    finally:
        # Cleanup
        if session_id in websocket_connections:
            del websocket_connections[session_id]
        
        logger.info(f"🧹 Cleaned up WebSocket for session {session_id}")


async def handle_websocket_message(session_id: str, message: dict, websocket: WebSocket):
    """Handle incoming WebSocket messages"""
    
    message_type = message.get("type")
    
    if message_type == "ping":
        # Ping/pong for connection testing
        response = {
            "type": "pong", 
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }
        await websocket.send_text(json.dumps(response))
        
    elif message_type == "text_message":
        await handle_text_message(session_id, message, websocket)
        
    elif message_type == "audio_data":
        await handle_audio_data_placeholder(session_id, message, websocket)
        
    elif message_type == "status_request":
        await handle_status_request(session_id, websocket)
        
    else:
        error_msg = {
            "type": "error",
            "session_id": session_id,
            "error_code": "UNKNOWN_MESSAGE_TYPE",
            "error_message": f"Unknown message type: {message_type}",
            "supported_types": ["ping", "text_message", "audio_data", "status_request"]
        }
        await websocket.send_text(json.dumps(error_msg))


async def handle_text_message(session_id: str, message: dict, websocket: WebSocket):
    """Handle text message for conversation"""
    
    try:
        text = message.get("text", "")
        if not text:
            return
        
        # Add to conversation
        session = active_sessions[session_id]
        session.add_message("user", text)
        
        # Simulate AI processing delay
        await asyncio.sleep(0.1)
        
        # Generate placeholder AI response
        ai_response = f"🤖 I received your message: '{text}'. This is a Phase 1 test response. In Phase 2, I'll have real speech recognition and natural voice synthesis!"
        session.add_message("assistant", ai_response)
        
        # Send response
        response_msg = {
            "type": "text_response",
            "session_id": session_id,
            "text": ai_response,
            "timestamp": datetime.now().isoformat()
        }
        await websocket.send_text(json.dumps(response_msg))
        
        logger.info(f"💬 Processed text message for session {session_id}")
        
    except Exception as e:
        logger.error(f"❌ Error processing text message: {e}")
        error_msg = {
            "type": "error",
            "session_id": session_id,
            "error_code": "TEXT_PROCESSING_ERROR", 
            "error_message": str(e)
        }
        await websocket.send_text(json.dumps(error_msg))


async def handle_audio_data_placeholder(session_id: str, message: dict, websocket: WebSocket):
    """Handle audio data (placeholder for Phase 1)"""
    
    try:
        # Simulate audio processing
        await asyncio.sleep(0.05)
        
        response_msg = {
            "type": "audio_processed",
            "session_id": session_id,
            "message": "Audio received and processed (Phase 1 placeholder)",
            "next_phase": "Real speech recognition will be added in Phase 2",
            "timestamp": datetime.now().isoformat()
        }
        await websocket.send_text(json.dumps(response_msg))
        
        logger.info(f"🎤 Processed audio placeholder for session {session_id}")
        
    except Exception as e:
        logger.error(f"❌ Error processing audio: {e}")


async def handle_status_request(session_id: str, websocket: WebSocket):
    """Handle status request"""
    
    session = active_sessions.get(session_id)
    if not session:
        return
    
    status_msg = {
        "type": "status",
        "session_id": session_id,
        "status": "active",
        "details": {
            "message_count": len(session.messages),
            "last_activity": session.last_activity.isoformat(),
            "session_duration": (datetime.now() - session.started_at).total_seconds(),
            "phase": "Phase 1 Testing"
        },
        "timestamp": datetime.now().isoformat()
    }
    await websocket.send_text(json.dumps(status_msg))


@app.get("/sessions")
async def list_sessions():
    """List all active sessions"""
    
    sessions_info = []
    for session_id, session in active_sessions.items():
        sessions_info.append({
            "session_id": session_id,
            "user_id": session.user_id,
            "status": session.status,
            "started_at": session.started_at.isoformat(),
            "message_count": len(session.messages),
            "connected": session_id in websocket_connections
        })
    
    return {
        "total_sessions": len(active_sessions),
        "active_websockets": len(websocket_connections),
        "sessions": sessions_info
    }


@app.get("/stats")
async def get_stats():
    """Get service statistics"""
    
    return {
        "service": "Real-time Conversational AI",
        "phase": "Phase 1 Testing",
        "uptime_seconds": time.time() - start_time,
        "statistics": {
            "total_sessions_created": len(active_sessions) + session_counter,
            "active_sessions": len(active_sessions),
            "active_websockets": len(websocket_connections),
            "total_messages": sum(len(s.messages) for s in active_sessions.values())
        },
        "phase_1_features": [
            "✅ FastAPI service",
            "✅ Session management", 
            "✅ WebSocket communication",
            "✅ Health monitoring",
            "✅ Basic message handling"
        ],
        "phase_2_planned": [
            "🚧 Real speech recognition (Whisper)",
            "🚧 Natural voice synthesis (XTTS)",
            "🚧 Voice activity detection",
            "🚧 Real-time audio streaming"
        ]
    }


@app.get("/test")
async def test_page():
    """Serve test page"""
    import os
    
    test_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "test_client.html")
    
    if os.path.exists(test_file):
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return HTMLResponse(content=content)
    else:
        return {"error": "Test page not found", "path": test_file}


@app.get("/simple")
async def simple_test_page():
    """Serve simple test page"""
    import os
    
    test_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "simple_test.html")
    
    if os.path.exists(test_file):
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return HTMLResponse(content=content)
    else:
        return {"error": "Simple test page not found", "path": test_file}


# Global counters
start_time = time.time()
session_counter = 0


if __name__ == "__main__":
    logger.info("🎙️ Starting Real-time Conversational AI - Phase 1 Test")
    uvicorn.run(
        "main_test:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    )
