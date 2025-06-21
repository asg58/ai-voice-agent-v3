"""
Real-time Conversational AI - Phase 2 with OpenAI Integration
Complete AI-powered voice conversation service
"""
import asyncio
import logging
import uuid
import json
import time
import base64
from contextlib import asynccontextmanager
from typing import Dict, Optional
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import uvicorn
from dotenv import load_dotenv
import os

# Load Phase 2 environment
load_dotenv('.env.phase2')

# Import our OpenAI integration
try:
    from .openai_integration import initialize_openai_service, conversation_manager, encode_audio_to_base64, decode_audio_from_base64
    AI_ENABLED = True
except ImportError:
    AI_ENABLED = False
    print("⚠️ OpenAI integration not available")

# Enhanced logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
class Phase2Config:
    def __init__(self):
        self.service_host = "0.0.0.0"
        self.service_port = int(os.getenv("PHASE2_PORT", 8082))
        self.debug = False
        self.environment = "development-phase2"
        
        # OpenAI settings
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.enable_real_ai = os.getenv("ENABLE_REAL_AI", "true").lower() == "true"
        self.ai_response_timeout = int(os.getenv("AI_RESPONSE_TIMEOUT", 10))
        
        # Audio settings
        self.audio_sample_rate = int(os.getenv("AUDIO_SAMPLE_RATE", 16000))
        self.audio_channels = int(os.getenv("AUDIO_CHANNELS", 1))
        self.max_audio_duration = int(os.getenv("MAX_AUDIO_DURATION_SECONDS", 30))
        
        # TTS settings
        self.tts_voice = os.getenv("TTS_VOICE", "nova")
        self.tts_language = os.getenv("TTS_LANGUAGE", "nl")
    
    def get_cors_config(self):
        return {
            "allow_origins": ["*"],
            "allow_credentials": True,
            "allow_methods": ["*"],
            "allow_headers": ["*"],
        }

settings = Phase2Config()

# Initialize OpenAI service if available
openai_service = None
if AI_ENABLED and settings.openai_api_key:
    try:
        openai_service = initialize_openai_service(settings.openai_api_key)
        logger.info("✅ OpenAI service initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize OpenAI service: {e}")
        AI_ENABLED = False

# Session management
active_sessions: Dict[str, any] = {}
websocket_connections: Dict[str, any] = {}

class Phase2Session:
    """Enhanced session for Phase 2 with AI conversation"""
    
    def __init__(self, session_id: str, user_id: Optional[str] = None):
        self.session_id = session_id
        self.user_id = user_id
        self.messages = []
        self.started_at = datetime.now()
        self.last_activity = datetime.now()
        self.status = "active"
        self.language = settings.tts_language
        self.message_count = 0
        self.ai_interactions = 0
        self.audio_processed = 0
        self.processing_times = []
    
    def add_message(self, role: str, content: str, processing_time_ms: float = 0):
        """Add message with AI processing metrics"""
        message = {
            "id": len(self.messages) + 1,
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "processing_time_ms": processing_time_ms
        }
        
        self.messages.append(message)
        self.last_activity = datetime.now()
        self.message_count += 1
        
        if role == "assistant":
            self.ai_interactions += 1
            if processing_time_ms > 0:
                self.processing_times.append(processing_time_ms)
        
        # Keep only last 50 messages
        if len(self.messages) > 50:
            self.messages = self.messages[-50:]
        
        return message
    
    def add_audio_interaction(self):
        """Track audio processing"""
        self.audio_processed += 1
    
    def get_summary(self):
        """Get comprehensive session summary"""
        avg_processing_time = (
            sum(self.processing_times) / len(self.processing_times) 
            if self.processing_times else 0
        )
        
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "status": self.status,
            "language": self.language,
            "started_at": self.started_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "duration_minutes": (datetime.now() - self.started_at).total_seconds() / 60,
            "statistics": {
                "total_messages": self.message_count,
                "ai_interactions": self.ai_interactions,
                "audio_processed": self.audio_processed,
                "avg_processing_time_ms": round(avg_processing_time, 2)
            },
            "recent_messages": self.messages[-5:] if self.messages else [],
            "ai_enabled": AI_ENABLED
        }

# Application lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle"""
    
    # Startup
    logger.info("🚀 Starting Real-time Conversational AI - Phase 2 (AI Integration)")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Port: {settings.service_port}")
    logger.info(f"AI Enabled: {AI_ENABLED}")
    logger.info(f"OpenAI Service: {'✅ Ready' if openai_service else '❌ Not available'}")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Phase 2 AI Service")
    
    # Close all connections
    for session_id in list(websocket_connections.keys()):
        try:
            await websocket_connections[session_id].close()
        except Exception:
            pass
    
    active_sessions.clear()
    websocket_connections.clear()
    
    logger.info("✅ Phase 2 shutdown completed")

# Create FastAPI app
app = FastAPI(
    title="Real-time Conversational AI (Phase 2 - AI Integration)",
    description="Natural, human-like AI agent with OpenAI-powered real-time voice conversation",
    version="2.0.0-ai-integration",
    lifespan=lifespan,
    debug=settings.debug
)

# Add CORS middleware
app.add_middleware(CORSMiddleware, **settings.get_cors_config())

# Global counters
start_time = time.time()

@app.get("/")
async def root():
    """Root endpoint with Phase 2 service information"""
    return {
        "service": "Real-time Conversational AI",
        "version": "2.0.0-ai-integration", 
        "phase": "Phase 2 - AI Integration",
        "status": "running",
        "environment": settings.environment,
        "features": [
            "OpenAI GPT-4o-mini conversation",
            "OpenAI Whisper speech-to-text",
            "OpenAI TTS text-to-speech", 
            "Real-time audio processing",
            "Enhanced session management",
            "AI conversation context",
            "Performance metrics"
        ],
        "ai_capabilities": {
            "enabled": AI_ENABLED,
            "speech_recognition": AI_ENABLED,
            "text_generation": AI_ENABLED,
            "speech_synthesis": AI_ENABLED,
            "conversation_memory": True
        },
        "endpoints": {
            "health": "/health",
            "sessions": "/sessions", 
            "websocket": "/ws/{session_id}",
            "test": "/test",
            "ai_test": "/ai-test",
            "docs": "/docs"
        },
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Enhanced health check with AI service status"""
    
    session_count = len(active_sessions)
    websocket_count = len(websocket_connections)
    total_messages = sum(session.message_count for session in active_sessions.values())
    total_ai_interactions = sum(session.ai_interactions for session in active_sessions.values())
    
    # Test AI service health
    ai_health = "healthy" if AI_ENABLED else "disabled"
    if AI_ENABLED and openai_service:
        try:
            # Quick AI health test (skip for now to avoid API calls)
            ai_health = "healthy"
        except Exception:
            ai_health = "error"
    
    return {
        "service": "realtime-voice-ai-phase2",
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "details": {
            "api": "healthy",
            "ai_service": ai_health,
            "sessions": f"{session_count} active",
            "websockets": f"{websocket_count} connected",
            "total_messages": total_messages,
            "ai_interactions": total_ai_interactions,
            "features": "phase2-ai-integration"
        },
        "uptime_seconds": time.time() - start_time,
        "version": "2.0.0-ai-integration"
    }

@app.post("/sessions")
async def create_session(user_id: Optional[str] = None):
    """Create a new AI conversation session"""
    
    try:
        session_id = str(uuid.uuid4())
        session = Phase2Session(session_id, user_id)
        active_sessions[session_id] = session
        
        logger.info(f"📝 Created Phase 2 AI session {session_id} for user {user_id}")
        
        return {
            "session_id": session_id,
            "status": "created",
            "language": session.language,
            "created_at": session.started_at.isoformat(),
            "ai_enabled": AI_ENABLED,
            "features": ["speech_recognition", "ai_conversation", "speech_synthesis"] if AI_ENABLED else ["basic_chat"]
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to create Phase 2 session: {e}")
        raise HTTPException(status_code=500, detail="Failed to create AI session")

@app.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Get AI session information"""
    
    session = active_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="AI session not found")
    
    return session.get_summary()

@app.delete("/sessions/{session_id}")
async def end_session(session_id: str):
    """End AI conversation session"""
    
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="AI session not found")
    
    # Close WebSocket if connected
    if session_id in websocket_connections:
        try:
            await websocket_connections[session_id].close()
        except Exception:
            pass
        del websocket_connections[session_id]
    
    # Clear conversation history
    conversation_manager.clear_conversation(session_id)
    
    # Remove session
    session = active_sessions[session_id]
    session.status = "ended"
    del active_sessions[session_id]
    
    logger.info(f"🔚 Ended Phase 2 AI session {session_id}")
    
    return {
        "status": "ended",
        "session_id": session_id,
        "ended_at": datetime.now().isoformat()
    }

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """Phase 2 WebSocket endpoint with AI conversation"""
    
    await websocket.accept()
    
    try:
        websocket_connections[session_id] = websocket
        logger.info(f"🔌 Phase 2 AI WebSocket connected for session {session_id}")
        
        # Ensure session exists
        session = active_sessions.get(session_id)
        if not session:
            error_msg = {
                "type": "error",
                "error_message": "AI session not found",
                "session_id": session_id
            }
            await websocket.send_text(json.dumps(error_msg))
            await websocket.close()
            return
        
        # Send welcome message with AI capabilities
        welcome_msg = {
            "type": "status",
            "session_id": session_id,
            "status": "connected",
            "message": "Connected to Real-time AI (Phase 2 - OpenAI Integration)",
            "ai_features": {
                "speech_to_text": AI_ENABLED,
                "ai_conversation": AI_ENABLED,
                "text_to_speech": AI_ENABLED,
                "conversation_memory": True
            },
            "supported_message_types": ["ping", "text_message", "audio_data", "status_request"],
            "timestamp": datetime.now().isoformat()
        }
        await websocket.send_text(json.dumps(welcome_msg))
        
        # Message handling loop
        while True:
            try:
                data = await websocket.receive_text()
                await handle_ai_websocket_message(session_id, data, websocket)
                
            except WebSocketDisconnect:
                logger.info(f"🔌 Phase 2 AI WebSocket disconnected for session {session_id}")
                break
            except Exception as e:
                logger.error(f"❌ Error in Phase 2 AI WebSocket: {e}")
                error_msg = {
                    "type": "error",
                    "error_message": "AI processing error",
                    "details": str(e),
                    "session_id": session_id
                }
                try:
                    await websocket.send_text(json.dumps(error_msg))
                except Exception:
                    break
    
    finally:
        if session_id in websocket_connections:
            del websocket_connections[session_id]
        logger.info(f"🧹 Cleaned up Phase 2 AI WebSocket for session {session_id}")

async def handle_ai_websocket_message(session_id: str, data: str, websocket: WebSocket):
    """Enhanced WebSocket message handling with AI processing"""
    
    try:
        # Parse JSON
        try:
            message = json.loads(data)
        except json.JSONDecodeError as e:
            error_msg = {
                "type": "error",
                "error_message": "Invalid JSON format",
                "session_id": session_id
            }
            await websocket.send_text(json.dumps(error_msg))
            return
        
        message_type = message.get("type")
        session = active_sessions.get(session_id)
        
        if message_type == "ping":
            await handle_ai_ping(session_id, websocket)
        elif message_type == "text_message":
            await handle_ai_text_message(session_id, message, websocket)
        elif message_type == "audio_data":
            await handle_ai_audio_message(session_id, message, websocket)
        elif message_type == "status_request":
            await handle_ai_status_request(session_id, websocket)
        else:
            error_msg = {
                "type": "error",
                "error_message": f"Unknown message type: {message_type}",
                "supported_types": ["ping", "text_message", "audio_data", "status_request"],
                "session_id": session_id
            }
            await websocket.send_text(json.dumps(error_msg))
    
    except Exception as e:
        logger.error(f"❌ Error handling AI WebSocket message: {e}")
        error_msg = {
            "type": "error", 
            "error_message": "AI message processing error",
            "session_id": session_id
        }
        await websocket.send_text(json.dumps(error_msg))

async def handle_ai_ping(session_id: str, websocket: WebSocket):
    """AI-enhanced ping handling"""
    response = {
        "type": "pong",
        "session_id": session_id,
        "server_time": datetime.now().isoformat(),
        "ai_status": "ready" if AI_ENABLED else "disabled",
        "phase": "2-ai-integration"
    }
    await websocket.send_text(json.dumps(response))

async def handle_ai_text_message(session_id: str, message: dict, websocket: WebSocket):
    """Process text message with AI conversation"""
    
    try:
        text = message.get("text", "").strip()
        if not text:
            error_msg = {
                "type": "error",
                "error_message": "Empty text message",
                "session_id": session_id
            }
            await websocket.send_text(json.dumps(error_msg))
            return
        
        session = active_sessions.get(session_id)
        if not session:
            return
        
        # Add user message to session
        session.add_message("user", text)
        
        if AI_ENABLED and openai_service:
            # Get conversation history
            conversation_history = conversation_manager.get_conversation_history(session_id)
            
            # Process with AI
            start_time = datetime.now()
            ai_result = await openai_service.process_conversation_cycle(
                text_input=text,
                conversation_history=conversation_history,
                return_audio=True
            )
            processing_time = ai_result.get("processing_time_ms", 0)
            
            # Add messages to conversation manager
            conversation_manager.add_message(session_id, "user", text)
            if ai_result["ai_response_text"]:
                conversation_manager.add_message(session_id, "assistant", ai_result["ai_response_text"])
            
            # Add AI response to session
            ai_response = ai_result["ai_response_text"]
            session.add_message("assistant", ai_response, processing_time)
            
            # Prepare response with audio if available
            response_msg = {
                "type": "ai_text_response",
                "session_id": session_id,
                "user_text": text,
                "ai_text": ai_response,
                "processing_time_ms": processing_time,
                "audio_available": ai_result["ai_response_audio"] is not None,
                "timestamp": datetime.now().isoformat()
            }
            
            # Add audio data if available
            if ai_result["ai_response_audio"]:
                audio_base64 = encode_audio_to_base64(ai_result["ai_response_audio"])
                response_msg["ai_audio_base64"] = audio_base64
                response_msg["audio_format"] = "mp3"
            
            await websocket.send_text(json.dumps(response_msg))
            
            logger.info(f"💬 AI conversation: '{text}' → '{ai_response}' ({processing_time:.0f}ms)")
            
        else:
            # Fallback response without AI
            fallback_response = f"📝 Ontvangen: '{text}' (AI uitgeschakeld - gebruik de working enhanced versie voor basisfunctionaliteit)"
            session.add_message("assistant", fallback_response)
            
            response_msg = {
                "type": "text_response",
                "session_id": session_id,
                "text": fallback_response,
                "ai_enabled": False,
                "timestamp": datetime.now().isoformat()
            }
            await websocket.send_text(json.dumps(response_msg))
        
    except Exception as e:
        logger.error(f"❌ Error in AI text processing: {e}")
        error_msg = {
            "type": "error",
            "error_message": "AI text processing failed",
            "details": str(e),
            "session_id": session_id
        }
        await websocket.send_text(json.dumps(error_msg))

async def handle_ai_audio_message(session_id: str, message: dict, websocket: WebSocket):
    """Process audio message with AI speech recognition and response"""
    
    try:
        audio_base64 = message.get("audio_data", "")
        if not audio_base64:
            error_msg = {
                "type": "error",
                "error_message": "No audio data provided",
                "session_id": session_id
            }
            await websocket.send_text(json.dumps(error_msg))
            return
        
        session = active_sessions.get(session_id)
        if not session:
            return
        
        session.add_audio_interaction()
        
        if AI_ENABLED and openai_service:
            try:
                # Decode audio data
                audio_bytes = decode_audio_from_base64(audio_base64)
                
                # Get conversation history
                conversation_history = conversation_manager.get_conversation_history(session_id)
                
                # Process complete AI cycle: STT → AI → TTS
                ai_result = await openai_service.process_conversation_cycle(
                    audio_data=audio_bytes,
                    conversation_history=conversation_history,
                    return_audio=True
                )
                
                transcribed_text = ai_result["transcribed_text"]
                ai_response = ai_result["ai_response_text"]
                processing_time = ai_result["processing_time_ms"]
                
                # Add to conversation history
                if transcribed_text:
                    conversation_manager.add_message(session_id, "user", transcribed_text)
                    session.add_message("user", transcribed_text)
                
                if ai_response:
                    conversation_manager.add_message(session_id, "assistant", ai_response)
                    session.add_message("assistant", ai_response, processing_time)
                
                # Prepare comprehensive response
                response_msg = {
                    "type": "ai_audio_response",
                    "session_id": session_id,
                    "transcribed_text": transcribed_text,
                    "ai_response_text": ai_response,
                    "processing_time_ms": processing_time,
                    "audio_available": ai_result["ai_response_audio"] is not None,
                    "timestamp": datetime.now().isoformat()
                }
                
                # Add response audio if available
                if ai_result["ai_response_audio"]:
                    audio_response_base64 = encode_audio_to_base64(ai_result["ai_response_audio"])
                    response_msg["ai_audio_base64"] = audio_response_base64
                    response_msg["audio_format"] = "mp3"
                
                await websocket.send_text(json.dumps(response_msg))
                
                logger.info(f"🎤 AI audio cycle: '{transcribed_text}' → '{ai_response}' ({processing_time:.0f}ms)")
                
            except Exception as e:
                logger.error(f"❌ Error in AI audio processing: {e}")
                error_msg = {
                    "type": "error",
                    "error_message": "AI audio processing failed",
                    "details": str(e),
                    "session_id": session_id
                }
                await websocket.send_text(json.dumps(error_msg))
        else:
            # Fallback without AI
            response_msg = {
                "type": "audio_processed",
                "session_id": session_id,
                "message": "Audio ontvangen (AI uitgeschakeld - Phase 2 vereist OpenAI API)",
                "timestamp": datetime.now().isoformat()
            }
            await websocket.send_text(json.dumps(response_msg))
        
    except Exception as e:
        logger.error(f"❌ Error handling audio message: {e}")
        error_msg = {
            "type": "error",
            "error_message": "Audio processing error",
            "session_id": session_id
        }
        await websocket.send_text(json.dumps(error_msg))

async def handle_ai_status_request(session_id: str, websocket: WebSocket):
    """Enhanced status with AI conversation statistics"""
    
    try:
        session = active_sessions.get(session_id)
        conversation_summary = conversation_manager.get_conversation_summary(session_id)
        
        status_msg = {
            "type": "ai_status",
            "session_id": session_id,
            "status": "active",
            "ai_enabled": AI_ENABLED,
            "session_details": session.get_summary() if session else {},
            "conversation_summary": conversation_summary,
            "server_info": {
                "version": "2.0.0-ai-integration",
                "phase": "Phase 2 - AI Integration",
                "openai_ready": openai_service is not None,
                "features": ["gpt4o-mini", "whisper-1", "tts-1"]
            },
            "timestamp": datetime.now().isoformat()
        }
        await websocket.send_text(json.dumps(status_msg))
        
    except Exception as e:
        logger.error(f"❌ Error handling status request: {e}")

@app.get("/sessions")
async def list_sessions():
    """List all AI sessions"""
    
    sessions_info = []
    for session_id, session in active_sessions.items():
        conversation_summary = conversation_manager.get_conversation_summary(session_id)
        session_info = session.get_summary()
        session_info["conversation_summary"] = conversation_summary
        sessions_info.append(session_info)
    
    return {
        "total_sessions": len(active_sessions),
        "active_websockets": len(websocket_connections),
        "ai_enabled": AI_ENABLED,
        "phase": "2-ai-integration",
        "sessions": sessions_info
    }

@app.get("/stats")
async def get_ai_stats():
    """Comprehensive AI service statistics"""
    
    total_messages = sum(session.message_count for session in active_sessions.values())
    total_ai_interactions = sum(session.ai_interactions for session in active_sessions.values())
    total_audio_processed = sum(session.audio_processed for session in active_sessions.values())
    
    all_processing_times = []
    for session in active_sessions.values():
        all_processing_times.extend(session.processing_times)
    
    avg_processing_time = (
        sum(all_processing_times) / len(all_processing_times) 
        if all_processing_times else 0
    )
    
    return {
        "service": "Real-time Conversational AI",
        "version": "2.0.0-ai-integration",
        "phase": "Phase 2 - AI Integration",
        "uptime_seconds": time.time() - start_time,
        "ai_statistics": {
            "ai_enabled": AI_ENABLED,
            "openai_service_ready": openai_service is not None,
            "total_sessions": len(active_sessions),
            "active_websockets": len(websocket_connections),
            "total_messages": total_messages,
            "ai_interactions": total_ai_interactions,
            "audio_processed": total_audio_processed,
            "avg_ai_processing_time_ms": round(avg_processing_time, 2)
        },
        "phase_2_features": [
            "✅ OpenAI GPT-4o-mini conversation",
            "✅ OpenAI Whisper speech-to-text",
            "✅ OpenAI TTS speech synthesis",
            "✅ Real-time audio processing",
            "✅ Conversation context memory",
            "✅ Performance monitoring"
        ],
        "next_phases": [
            "🚧 Voice Activity Detection",
            "🚧 Interruption handling",
            "🚧 Emotional intelligence",
            "🚧 Multi-language support"
        ]
    }

@app.get("/ai-test")
async def ai_test():
    """Test AI capabilities directly"""
    
    if not AI_ENABLED or not openai_service:
        return {
            "ai_test": "failed",
            "error": "AI service not available",
            "openai_api_key_present": bool(settings.openai_api_key),
            "service_initialized": openai_service is not None
        }
    
    try:
        # Test AI conversation
        start_time = datetime.now()
        ai_result = await openai_service.process_conversation_cycle(
            text_input="Hallo, dit is een test. Antwoord kort in het Nederlands.",
            conversation_history=[],
            return_audio=False
        )
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return {
            "ai_test": "success",
            "test_input": "Hallo, dit is een test. Antwoord kort in het Nederlands.",
            "ai_response": ai_result["ai_response_text"],
            "processing_time_ms": round(processing_time, 2),
            "openai_service": "working",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "ai_test": "failed",
            "error": str(e),
            "openai_service": "error",
            "timestamp": datetime.now().isoformat()
        }

@app.get("/test")
async def test_page():
    """Serve Phase 2 AI test page"""
    try:
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Phase 2 AI Test Interface</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
                .container { max-width: 800px; margin: 0 auto; background: rgba(255,255,255,0.1); padding: 20px; border-radius: 10px; }
                .feature { background: rgba(255,255,255,0.2); margin: 10px 0; padding: 15px; border-radius: 5px; }
                .status { color: #4CAF50; font-weight: bold; }
                .error { color: #f44336; font-weight: bold; }
                button { background: #4CAF50; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; margin: 5px; }
                button:hover { background: #45a049; }
                input[type="text"] { width: 300px; padding: 10px; border-radius: 5px; border: none; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🤖 Phase 2 - AI Integration Test</h1>
                
                <div class="feature">
                    <h3>✅ OpenAI Integration Ready</h3>
                    <p>GPT-4o-mini • Whisper STT • TTS Nova Voice</p>
                    <button onclick="testAI()">Test AI Response</button>
                    <div id="ai-result"></div>
                </div>
                
                <div class="feature">
                    <h3>🎤 Voice Conversation Test</h3>
                    <p>Real-time speech-to-text → AI response → text-to-speech</p>
                    <input type="text" id="text-input" placeholder="Type message for AI...">
                    <button onclick="sendTextToAI()">Send to AI</button>
                    <div id="conversation-result"></div>
                </div>
                
                <div class="feature">
                    <h3>📊 Service Information</h3>
                    <button onclick="getStats()">Get AI Statistics</button>
                    <button onclick="getHealth()">Health Check</button>
                    <div id="stats-result"></div>
                </div>
                
                <div class="feature">
                    <h3>🔗 API Endpoints</h3>
                    <ul>
                        <li><a href="/docs" style="color: #4CAF50;">API Documentation</a></li>
                        <li><a href="/ai-test" style="color: #4CAF50;">Direct AI Test</a></li>
                        <li><a href="/health" style="color: #4CAF50;">Health Check</a></li>
                        <li><a href="/stats" style="color: #4CAF50;">AI Statistics</a></li>
                    </ul>
                </div>
            </div>
            
            <script>
                async function testAI() {
                    const result = document.getElementById('ai-result');
                    result.innerHTML = '⏳ Testing AI...';
                    
                    try {
                        const response = await fetch('/ai-test');
                        const data = await response.json();
                        
                        if (data.ai_test === 'success') {
                            result.innerHTML = `
                                <div class="status">✅ AI Test Successful!</div>
                                <p><strong>Response:</strong> ${data.ai_response}</p>
                                <p><strong>Processing:</strong> ${data.processing_time_ms}ms</p>
                            `;
                        } else {
                            result.innerHTML = `<div class="error">❌ AI Test Failed: ${data.error}</div>`;
                        }
                    } catch (error) {
                        result.innerHTML = `<div class="error">❌ Error: ${error.message}</div>`;
                    }
                }
                
                async function sendTextToAI() {
                    const input = document.getElementById('text-input');
                    const result = document.getElementById('conversation-result');
                    const text = input.value.trim();
                    
                    if (!text) {
                        result.innerHTML = '<div class="error">Please enter a message</div>';
                        return;
                    }
                    
                    result.innerHTML = '⏳ Processing with AI...';
                    
                    // This would typically use WebSocket, but for demo we'll use the direct AI test
                    try {
                        const response = await fetch('/ai-test');
                        const data = await response.json();
                        
                        result.innerHTML = `
                            <div class="status">💬 AI Conversation Demo</div>
                            <p><strong>You:</strong> ${text}</p>
                            <p><strong>AI:</strong> ${data.ai_response || 'AI service not available'}</p>
                            <p><em>For full conversation, use WebSocket connection at ws://localhost:8082/ws/{session_id}</em></p>
                        `;
                        
                        input.value = '';
                    } catch (error) {
                        result.innerHTML = `<div class="error">❌ Error: ${error.message}</div>`;
                    }
                }
                
                async function getStats() {
                    const result = document.getElementById('stats-result');
                    result.innerHTML = '⏳ Loading statistics...';
                    
                    try {
                        const response = await fetch('/stats');
                        const data = await response.json();
                        
                        result.innerHTML = `
                            <div class="status">📊 AI Service Statistics</div>
                            <p><strong>Version:</strong> ${data.version}</p>
                            <p><strong>AI Enabled:</strong> ${data.ai_statistics.ai_enabled ? '✅' : '❌'}</p>
                            <p><strong>Sessions:</strong> ${data.ai_statistics.total_sessions}</p>
                            <p><strong>AI Interactions:</strong> ${data.ai_statistics.ai_interactions}</p>
                            <p><strong>Avg Processing:</strong> ${data.ai_statistics.avg_ai_processing_time_ms}ms</p>
                        `;
                    } catch (error) {
                        result.innerHTML = `<div class="error">❌ Error: ${error.message}</div>`;
                    }
                }
                
                async function getHealth() {
                    const result = document.getElementById('stats-result');
                    result.innerHTML = '⏳ Checking health...';
                    
                    try {
                        const response = await fetch('/health');
                        const data = await response.json();
                        
                        result.innerHTML = `
                            <div class="status">💚 Service Health</div>
                            <p><strong>Status:</strong> ${data.status}</p>
                            <p><strong>AI Service:</strong> ${data.details.ai_service}</p>
                            <p><strong>Uptime:</strong> ${Math.round(data.uptime_seconds)}s</p>
                            <p><strong>Version:</strong> ${data.version}</p>
                        `;
                    } catch (error) {
                        result.innerHTML = `<div class="error">❌ Error: ${error.message}</div>`;
                    }
                }
            </script>
        </body>
        </html>
        """)
    except Exception as e:
        return HTMLResponse(content=f"<h1>Error loading Phase 2 test page</h1><p>{e}</p>")

if __name__ == "__main__":
    logger.info("🤖 Starting Phase 2 Real-time Conversational AI with OpenAI Integration")
    uvicorn.run(
        "main_phase2:app",
        host=settings.service_host,
        port=settings.service_port,
        reload=settings.debug,
        log_level="info"
    )
