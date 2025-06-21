#!/usr/bin/env python3
"""
Simple Test Server - Bypassing AI Models
Voor snelle basis functionaliteit testing zonder zware modellen
"""
import json
import uuid
import logging
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Simpele in-memory session store
sessions = {}

app = FastAPI(
    title="AI Voice Test Server (Simple Mode)",
    description="Lightweight server for testing basic functionality",
    version="1.0.0-test"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "AI Voice Test Server (Simple Mode)",
        "version": "1.0.0-test",
        "status": "running",
        "message": "Server running in simple test mode - all AI models bypassed",
        "endpoints": {
            "health": "/health",
            "sessions": "/sessions",
            "websocket": "/ws/{session_id}"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0-test",
        "components": {
            "server": True,
            "websocket": True,
            "session_manager": True,
            "ai_models": "bypassed"
        },
        "active_sessions": len(sessions),
        "message": "All systems operational (simple mode)"
    }

@app.post("/sessions")
async def create_session(user_id: str = None):
    """Create a new session"""
    session_id = str(uuid.uuid4())
    session = {
        "session_id": session_id,
        "user_id": user_id or "anonymous",
        "created_at": datetime.now().isoformat(),
        "status": "active"
    }
    sessions[session_id] = session
    return session

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time communication"""
    await websocket.accept()
    
    # Send welcome message
    welcome_msg = {
        "type": "status",
        "status": "connected",
        "message": f"Connected to session {session_id} (simple mode)",
        "timestamp": datetime.now().isoformat(),
        "session_id": session_id
    }
    await websocket.send_text(json.dumps(welcome_msg))
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Process different message types
            response = await process_message(message, session_id)
            
            if response:
                await websocket.send_text(json.dumps(response))                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}")
        error_msg = {
            "type": "error",
            "error_message": str(e),
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id
        }
        await websocket.send_text(json.dumps(error_msg))

async def process_message(message: dict, session_id: str) -> dict:
    """Process incoming WebSocket messages"""
    msg_type = message.get("type", "unknown")
    timestamp = datetime.now().isoformat()
    
    if msg_type == "ping":
        return {
            "type": "pong",
            "timestamp": timestamp,
            "session_id": session_id
        }
    
    elif msg_type == "text_message":
        text = message.get("text", "")
        return {
            "type": "text_response",
            "text": f"Echo (simple mode): {text}",
            "timestamp": timestamp,
            "session_id": session_id
        }
    
    elif msg_type == "audio_data":
        return {
            "type": "audio_processed", 
            "message": "Audio received and processed (simulated)",
            "timestamp": timestamp,
            "session_id": session_id
        }
    
    elif msg_type == "status_request":
        return {
            "type": "status",
            "status": "active",
            "message": "Server running in simple test mode",
            "session_id": session_id,
            "timestamp": timestamp
        }
    
    else:
        return {
            "type": "error",
            "error_message": f"Unknown message type: {msg_type}",
            "timestamp": timestamp,
            "session_id": session_id
        }

if __name__ == "__main__":
    import uvicorn
    logger.info("🧪 Starting Simple Test Server...")
    logger.info("📋 Available endpoints:")
    logger.info("  - GET  /         (root)")
    logger.info("  - GET  /health   (health check)")
    logger.info("  - POST /sessions (create session)")
    logger.info("  - WS   /ws/{session_id} (websocket)")
    logger.info("🔗 Server will be available at: http://localhost:8080")
    logger.info("💡 Running in SIMPLE MODE - all AI models bypassed")
    
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
