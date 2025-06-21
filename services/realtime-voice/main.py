"""
Real-time Voice AI Service - CONSOLIDATED MAIN
Main FastAPI application entry point
Consolidated from multiple versions into one authoritative entry point
"""
import asyncio
import logging
import os
import sys
import time
import uuid
from typing import Dict, Optional
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Body, status, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
import uvicorn

# Add src directory to path for imports
src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
sys.path.insert(0, src_path)

# Import application components
from config.settings import VERSION, CORS_ORIGINS, HOST, PORT, DEBUG
from models import (
    SessionInfo, 
    ConversationSession, 
    AudioChunk, 
    MemoryCapabilities
)
from core.audio.pipeline import AudioProcessingPipeline
from core.memory.manager import memory_manager
from core.utils.metrics import metrics_manager
from core.utils.logging_config import configure_logging

# Configure logging
configure_logging()
logger = logging.getLogger(__name__)

# Global variables
audio_pipeline = None
active_sessions = {}
session_locks = {}


class VoiceAIService:
    """Main Voice AI Service class for better organization"""
    
    def __init__(self):
        self.audio_pipeline = None
        self.active_sessions = {}
        self.session_locks = {}
        self.start_time = None
        
    async def initialize_components(self):
        """Initialize all application components with graceful fallbacks"""
        logger.info("Initializing Voice AI Service components...")
        
        # Initialize memory backends
        try:
            await memory_manager.initialize()
            logger.info("Memory manager initialized successfully")
        except Exception as e:
            logger.warning(f"Memory manager initialization failed, continuing without: {e}")
        
        # Initialize event publisher
        try:
            from core.events.event_publisher import event_publisher
            await event_publisher.initialize()
            logger.info("Event publisher initialized successfully")
        except Exception as e:
            logger.warning(f"Event publisher initialization failed, continuing without: {e}")
        
        # Initialize audio pipeline
        try:
            self.audio_pipeline = AudioProcessingPipeline()
            await self.audio_pipeline.initialize()
            logger.info("Audio pipeline initialized successfully")
        except Exception as e:
            logger.warning(f"Audio pipeline initialization failed, using mock pipeline: {e}")
            # Create a minimal mock pipeline for testing
            self.audio_pipeline = type('MockPipeline', (), {
                'process_audio': lambda self, chunk: None,
                'process_text': lambda self, session_id, text: None,
                'reset_conversation': lambda self, session_id: None,
                'shutdown': lambda self: None
            })()
        
        # Initialize optimized pipeline
        try:
            from core.audio.optimized_pipeline import optimized_pipeline
            await optimized_pipeline.start()
            logger.info("Started optimized audio processing pipeline")
        except Exception as e:
            logger.warning(f"Optimized pipeline initialization failed: {e}")
            
        # Initialize enhanced WebSocket manager
        try:
            from core.websocket.enhanced_manager import enhanced_websocket_manager
            redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
            enhanced_websocket_manager.redis_client = None  # Will be set if Redis is available
            try:
                import redis
                enhanced_websocket_manager.redis_client = redis.from_url(redis_url)
                await enhanced_websocket_manager.start()
                logger.info("Started enhanced WebSocket manager with Redis")
            except ImportError:
                await enhanced_websocket_manager.start()
                logger.info("Started enhanced WebSocket manager without Redis")
        except Exception as e:
            logger.warning(f"Enhanced WebSocket manager initialization failed: {e}")
            
        # Initialize advanced metrics
        try:
            from core.monitoring.advanced_metrics import metrics_collector
            asyncio.create_task(metrics_collector())
            logger.info("Started advanced metrics collection")
        except Exception as e:
            logger.warning(f"Advanced metrics initialization failed: {e}")
        
        # Initialize conversation analysis
        try:
            from core.conversation.conversation_analysis import conversation_analysis
            await conversation_analysis.initialize()
            logger.info("Conversation analysis initialized successfully")
        except Exception as e:
            logger.warning(f"Conversation analysis initialization failed: {e}")
        
        # Initialize emotion recognition
        try:
            from core.audio.emotion_recognition import emotion_recognition
            await emotion_recognition.initialize()
            logger.info("Emotion recognition initialized successfully")
        except Exception as e:
            logger.warning(f"Emotion recognition initialization failed: {e}")
        
        # Initialize translation
        try:
            from core.translation.translator import translator
            await translator.initialize()
            logger.info("Translation service initialized successfully")
        except Exception as e:
            logger.warning(f"Translation initialization failed: {e}")
        
        # Initialize metrics
        try:
            metrics_manager.initialize()
            logger.info("Metrics manager initialized successfully")
        except Exception as e:
            logger.warning(f"Metrics manager initialization failed: {e}")
            
        logger.info("Component initialization completed (some components may be in fallback mode)")
    
    async def shutdown_components(self):
        """Shutdown all components gracefully"""
        logger.info("Shutting down Voice AI Service...")
        
        if self.audio_pipeline:
            try:
                await self.audio_pipeline.shutdown()
                logger.info("Audio pipeline shutdown complete")
            except Exception as e:
                logger.error(f"Error shutting down audio pipeline: {e}")
        
        # Close any active sessions
        for session_id in list(self.active_sessions.keys()):
            try:
                await self.close_session(session_id)
            except Exception as e:
                logger.error(f"Error closing session {session_id}: {e}")
        
        # Close memory manager
        try:
            await memory_manager.close()
            logger.info("Memory manager closed")
        except Exception as e:
            logger.error(f"Error closing memory manager: {e}")
        
        # Close event publisher
        try:
            from core.events.event_publisher import event_publisher
            await event_publisher.close()
            logger.info("Event publisher closed")
        except Exception as e:
            logger.error(f"Error closing event publisher: {e}")
        
        # Close conversation analysis
        try:
            from core.conversation.conversation_analysis import conversation_analysis
            conversation_analysis.close()
            logger.info("Conversation analysis closed")
        except Exception as e:
            logger.error(f"Error closing conversation analysis: {e}")
        
        # Close emotion recognition
        try:
            from core.audio.emotion_recognition import emotion_recognition
            emotion_recognition.close()
            logger.info("Emotion recognition closed")
        except Exception as e:
            logger.error(f"Error closing emotion recognition: {e}")
        
        # Close translation
        try:
            from core.translation.translator import translator
            translator.close()
            logger.info("Translation service closed")
        except Exception as e:
            logger.error(f"Error closing translation service: {e}")
        
        logger.info("Voice AI Service shutdown complete")
    
    async def close_session(self, session_id: str):
        """Close and clean up a session"""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            
            # Reset conversation in audio pipeline
            if self.audio_pipeline:
                try:
                    self.audio_pipeline.reset_conversation(session_id)
                except Exception as e:
                    logger.error(f"Error resetting conversation for session {session_id}: {e}")
            
            # Publish session ended event
            try:
                from core.events.event_publisher import event_publisher
                await event_publisher.publish_session_ended(session)
            except Exception as e:
                logger.error(f"Error publishing session ended event: {e}")
            
            # Remove session
            del self.active_sessions[session_id]
            if session_id in self.session_locks:
                del self.session_locks[session_id]
            
            logger.info(f"Session {session_id} closed and cleaned up")


# Create service instance
voice_ai_service = VoiceAIService()

# Define application lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events"""
    # Startup
    logger.info("Starting Voice AI Service...")
    
    # Set start time
    voice_ai_service.start_time = datetime.now()
    app.state.start_time = voice_ai_service.start_time
    
    # Initialize components
    await voice_ai_service.initialize_components()
    
    # Update global variables for backward compatibility
    global audio_pipeline, active_sessions, session_locks
    audio_pipeline = voice_ai_service.audio_pipeline
    active_sessions = voice_ai_service.active_sessions
    session_locks = voice_ai_service.session_locks
    
    logger.info("Voice AI Service is ready!")
    yield
    
    # Shutdown
    await voice_ai_service.shutdown_components()


# Create FastAPI app
app = FastAPI(
    title="Voice AI Service - Consolidated",
    description="Real-time Voice AI Service with Speech-to-Text and Text-to-Speech capabilities",
    version=VERSION,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define paths for static files and templates
static_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
templates_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")

# Create directories if they don't exist
os.makedirs(static_path, exist_ok=True)
os.makedirs(templates_path, exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=static_path), name="static")

# Initialize templates
templates = Jinja2Templates(directory=templates_path)


# === UI ENDPOINTS ===

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Root endpoint with dashboard UI"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Dashboard UI endpoint"""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "dashboard_mode": True
    })


@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    """Admin dashboard UI endpoint"""
    # In a real implementation, you would add authentication here
    return templates.TemplateResponse("index.html", {
        "request": request,
        "admin_mode": True
    })


# === API INFO & HEALTH ENDPOINTS ===

@app.get("/api/info")
async def api_info():
    """API information endpoint"""
    return {
        "service": "Voice AI Service - Consolidated Version",
        "status": "running",
        "version": VERSION,
        "consolidation_date": "2025-06-20",
        "endpoints": {
            "health": "/health",
            "session": "/session",
            "websocket": "/ws/{session_id}"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    # Get uptime
    uptime_seconds = (
        datetime.now() - app.state.start_time
    ).total_seconds() if hasattr(app.state, "start_time") else 0
    
    # Get statistics
    statistics = {
        "sessions": len(active_sessions),
        "uptime_seconds": uptime_seconds
    }
    
    # Check memory manager health
    try:
        memory_health = await memory_manager.health_check()
    except Exception as e:
        logger.error(f"Memory health check failed: {e}")
        memory_health = "error"
    
    return {
        "status": "healthy",
        "version": "consolidated",
        "timestamp": str(datetime.now()),
        "components": {
            "api": "ok",
            "audio_pipeline": "ok" if audio_pipeline else "not_initialized",
            "memory": memory_health
        },
        "statistics": statistics,
        "uptime_seconds": uptime_seconds
    }


@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check including component status"""
    try:
        from core.monitoring.advanced_metrics import voice_ai_metrics
        
        # Check various components
        health_status = {
            "overall": "healthy",
            "version": "consolidated",
            "components": {
                "audio_pipeline": "healthy" if audio_pipeline else "down",
                "memory_manager": "healthy",  # Could add actual checks
                "websocket_manager": "healthy",
                "metrics_collector": "healthy"
            },
            "metrics": {
                "active_connections": voice_ai_metrics.get_metric("websocket_connections_active", 0),
                "uptime": time.time() - app.state.start_time.timestamp()
            },
            "timestamp": time.time()
        }
        
        # Determine overall health
        component_statuses = list(health_status["components"].values())
        if "down" in component_statuses:
            health_status["overall"] = "degraded"
        elif "error" in component_statuses:
            health_status["overall"] = "critical"
            
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "overall": "critical",
            "error": str(e),
            "timestamp": time.time()
        }


# === SESSION MANAGEMENT ENDPOINTS ===

@app.post("/session", response_model=SessionInfo)
async def create_session(user_id: Optional[str] = None):
    """Create a new conversation session"""
    try:
        session_id = str(uuid.uuid4())
        user_id = user_id or f"user_{session_id[:8]}"
        
        # Create session
        session = ConversationSession(
            session_id=session_id,
            user_id=user_id,
            created_at=datetime.now()
        )
        
        # Store session
        active_sessions[session_id] = session
        session_locks[session_id] = asyncio.Lock()
        
        # Publish session created event
        try:
            from core.events.event_publisher import event_publisher
            await event_publisher.publish_session_created(session)
        except Exception as e:
            logger.warning(f"Failed to publish session created event: {e}")
        
        logger.info(f"Created session {session_id} for user {user_id}")
        return SessionInfo(
            session_id=session_id,
            user_id=user_id,
            created_at=session.created_at
        )
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        raise HTTPException(status_code=500, detail="Failed to create session")


@app.get("/session/{session_id}", response_model=SessionInfo)
async def get_session(session_id: str):
    """Get information about an existing session"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    try:
        session = active_sessions[session_id]
        
        # Get language from language detector
        language = "nl"  # Default
        try:
            from core.audio.language_detection import language_detector
            language = language_detector.get_session_language(session_id)
        except Exception as e:
            logger.warning(f"Failed to get session language: {e}")
        
        return SessionInfo(
            session_id=session.session_id,
            user_id=session.user_id,
            created_at=session.created_at,
            language=language,
            verified=getattr(session, 'verified', False),
            emotion=getattr(session, 'current_emotion', None),
            emotion_score=getattr(session, 'emotion_score', None),
            target_language=getattr(session, 'target_language', None),
            auto_translate=getattr(session, 'auto_translate', False)
        )
    except Exception as e:
        logger.error(f"Error getting session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get session information")


@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Delete an existing session"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    try:
        await voice_ai_service.close_session(session_id)
        return {"status": "success", "message": f"Session {session_id} deleted"}
    except Exception as e:
        logger.error(f"Error deleting session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete session")


@app.get("/sessions")
async def get_active_sessions():
    """Get list of active sessions"""
    try:
        sessions = []
        for session_id, session in active_sessions.items():
            sessions.append({
                "session_id": session_id,
                "user_id": session.user_id,
                "created_at": session.created_at,
                "verified": getattr(session, 'verified', False)
            })
        
        return {
            "sessions": sessions,
            "total": len(sessions)
        }
    except Exception as e:
        logger.error(f"Error getting active sessions: {e}")
        raise HTTPException(status_code=500, detail="Failed to get active sessions")


# === WEBSOCKET ENDPOINT ===

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time voice communication"""
    # Check if session exists
    if session_id not in active_sessions:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Session not found")
        return
    
    session = active_sessions[session_id]
    await websocket.accept()
    
    logger.info(f"WebSocket connection established for session {session_id}")
    
    try:
        # Update metrics
        try:
            from core.monitoring.advanced_metrics import voice_ai_metrics
            voice_ai_metrics.increment_counter("websocket_connections_total")
            voice_ai_metrics.increment_gauge("websocket_connections_active")
        except Exception as e:
            logger.warning(f"Failed to update WebSocket metrics: {e}")
        
        # Send connection established message
        await websocket.send_json({
            "type": "connection_established",
            "session_id": session_id,
            "timestamp": time.time()
        })
        
        while True:
            try:
                # Receive data from WebSocket
                data = await websocket.receive()
                
                if "text" in data:
                    # Handle text message
                    try:
                        import json
                        message_data = json.loads(data["text"])
                        await process_text_message(websocket, session, message_data)
                    except json.JSONDecodeError:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Invalid JSON format"
                        })
                elif "bytes" in data:
                    # Handle audio data
                    await process_audio_message(websocket, session, data["bytes"])
                
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected for session {session_id}")
                break
            except Exception as e:
                logger.error(f"Error processing WebSocket message for session {session_id}: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": "Error processing message"
                })
    
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}")
    
    finally:
        # Update metrics
        try:
            from core.monitoring.advanced_metrics import voice_ai_metrics
            voice_ai_metrics.decrement_gauge("websocket_connections_active")
        except Exception as e:
            logger.warning(f"Failed to update WebSocket metrics on disconnect: {e}")
        
        logger.info(f"WebSocket connection closed for session {session_id}")


async def process_text_message(websocket: WebSocket, session: ConversationSession, data: Dict):
    """Process text message from WebSocket"""
    try:
        message_type = data.get("type", "")
        
        if message_type == "text_message":
            text = data.get("text", "")
            if text and audio_pipeline:
                # Process text through pipeline
                result = audio_pipeline.process_text(session.session_id, text)
                if result:
                    await websocket.send_json({
                        "type": "text_response",
                        "text": result,
                        "timestamp": time.time()
                    })
                else:
                    await websocket.send_json({
                        "type": "text_response", 
                        "text": f"Echo: {text}",
                        "timestamp": time.time()
                    })
        
        elif message_type == "ping":
            await websocket.send_json({
                "type": "pong",
                "timestamp": time.time()
            })
        
        elif message_type == "status":
            await websocket.send_json({
                "type": "status_response",
                "session_id": session.session_id,
                "user_id": session.user_id,
                "connected": True,
                "timestamp": time.time()
            })
        
        else:
            await websocket.send_json({
                "type": "error",
                "message": f"Unknown message type: {message_type}"
            })
    
    except Exception as e:
        logger.error(f"Error processing text message: {e}")
        await websocket.send_json({
            "type": "error",
            "message": "Error processing text message"
        })


async def process_audio_message(websocket: WebSocket, session: ConversationSession, audio_data: bytes):
    """Process audio message from WebSocket"""
    if not audio_data:
        return
    
    try:
        # Acquire session lock to prevent concurrent processing
        async with session_locks[session.session_id]:
            if audio_pipeline:
                # Create audio chunk
                audio_chunk = AudioChunk(
                    data=audio_data,
                    timestamp=time.time(),
                    session_id=session.session_id
                )
                
                # Process audio through pipeline
                result = await audio_pipeline.process_audio(audio_chunk)
                
                if result:
                    await websocket.send_json({
                        "type": "transcription",
                        "text": result.get("text", ""),
                        "confidence": result.get("confidence", 0.0),
                        "timestamp": time.time()
                    })
            else:
                # Mock response for testing
                await websocket.send_json({
                    "type": "audio_received",
                    "size": len(audio_data),
                    "timestamp": time.time()
                })
    
    except Exception as e:
        logger.error(f"Error processing audio message: {e}")
        await websocket.send_json({
            "type": "error",
            "message": "Error processing audio"
        })


# === STATISTICS & METRICS ENDPOINTS ===

@app.get("/stats")
async def get_statistics():
    """Get system statistics"""
    try:
        uptime_seconds = (
            datetime.now() - app.state.start_time
        ).total_seconds() if hasattr(app.state, "start_time") else 0
        
        return {
            "service": "Voice AI Service - Consolidated",
            "version": VERSION,
            "uptime_seconds": uptime_seconds,
            "active_sessions": len(active_sessions),
            "total_sessions_created": len(active_sessions),  # This would be tracked differently in production
            "memory_usage": "N/A",  # Could add actual memory usage
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get statistics")


@app.get("/memory/capabilities", response_model=MemoryCapabilities)
async def get_memory_capabilities():
    """Get memory system capabilities"""
    try:
        capabilities = await memory_manager.get_capabilities()
        return capabilities
    except Exception as e:
        logger.error(f"Error getting memory capabilities: {e}")
        # Return default capabilities
        return MemoryCapabilities(
            max_context_length=4096,
            supports_embeddings=False,
            supports_semantic_search=False,
            supports_conversation_history=True
        )


# Run the application
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=HOST, 
        port=PORT,
        reload=DEBUG
    )