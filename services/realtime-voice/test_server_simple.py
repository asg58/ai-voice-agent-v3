#!/usr/bin/env python3
"""
Simple test server voor basis functionaliteit testing
Zonder zware AI modellen - alleen voor WebSocket en API tests
"""
import json
import uuid
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Simpele in-memory session store
sessions = {}

app = FastAPI(
    title="Simple Real-time Voice AI Test Server",
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
        "service": "Simple Real-time Voice AI Test Server",
        "version": "1.0.0-test",
        "status": "running",
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
            "websocket": True
        },
        "active_sessions": len(sessions)
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
        "message": f"Connected to session {session_id}",
        "timestamp": datetime.now().isoformat()
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
        print(f"WebSocket disconnected: {session_id}")
    except Exception as e:
        error_msg = {
            "type": "error",
            "error_message": str(e),
            "timestamp": datetime.now().isoformat()
        }
        await websocket.send_text(json.dumps(error_msg))

async def process_message(message: dict, session_id: str) -> dict:
    """Process incoming WebSocket messages"""
    msg_type = message.get("type", "unknown")
    timestamp = datetime.now().isoformat()
    
    if msg_type == "ping":
        return {
            "type": "pong",
            "timestamp": timestamp
        }
    
    elif msg_type == "text_message":
        text = message.get("text", "")
        return {
            "type": "text_response",
            "text": f"Echo: {text}",
            "timestamp": timestamp
        }
    
    elif msg_type == "audio_data":
        return {
            "type": "audio_processed",
            "message": "Audio received (simulated processing)",
            "timestamp": timestamp
        }
    
    elif msg_type == "status_request":
        return {
            "type": "status",
            "status": "active",
            "message": "Server is running normally",
            "session_id": session_id,
            "timestamp": timestamp
        }
    
    else:
        return {
            "type": "error",
            "error_message": f"Unknown message type: {msg_type}",
            "timestamp": timestamp
        }

if __name__ == "__main__":
    import uvicorn
    print("🧪 Starting Simple Test Server...")
    print("📋 Available endpoints:")
    print("  - GET  /         (root)")
    print("  - GET  /health   (health check)")
    print("  - POST /sessions (create session)")
    print("  - WS   /ws/{session_id} (websocket)")
    print("\n🔗 Server will be available at: http://localhost:8081")
    
    uvicorn.run(app, host="0.0.0.0", port=8081, log_level="info")
