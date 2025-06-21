"""
Real-time Conversational AI - Phase 2 Complete Service (PROFESSIONAL)
Integrates STT, TTS, LLM, and Audio Pipeline for full functionality
"""
import time
import json
import uuid
import base64
import logging
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import uvicorn

from .config_enhanced import settings
from .models import (
    ConversationSession, HealthCheckResult, AudioChunk, TTSRequest
)
from .session_manager import session_manager
from .validation import validate_message
from .error_handling import ErrorHandler
from .audio_pipeline import audio_pipeline
from .stt_engine import stt_engine
from .tts_engine import tts_engine
from .conversation_manager import conversation_manager
from .vad_detector import vad_detector

logging.basicConfig(
    level=getattr(logging, settings.service.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

error_handler = ErrorHandler()


# Application lifespan with Phase 2 initialization
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle with Phase 2 components"""
    logger.info("🚀 Starting Real-time Conversational AI - Phase 2 (PROFESSIONAL)")
    try:
        # Initialize all professional components
        await session_manager.initialize()
        await vad_detector.initialize()
        await stt_engine.initialize()
        await tts_engine.initialize()
        await conversation_manager.initialize()
        await audio_pipeline.initialize()
        logger.info("✅ All Phase 2 components initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize components: {e}")
    yield
    # Shutdown
    logger.info("🛑 Shutting down Real-time Conversational AI")
    try:
        await audio_pipeline.cleanup()
        await conversation_manager.cleanup()
        await tts_engine.cleanup()
        await stt_engine.cleanup()
        await vad_detector.cleanup()
        await session_manager.cleanup()
        logger.info("✅ Cleanup completed")
    except Exception as e:
        logger.error(f"❌ Error during cleanup: {e}")


# Create FastAPI application with lifespan
app = FastAPI(
    title="Real-time Conversational AI - Phase 2",
    description="Natural conversation AI with STT, TTS, and LLM integration",
    version="2.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    **settings.get_cors_config()
)


@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "Real-time Conversational AI",
        "version": "2.0.0",
        "phase": "Phase 2 - Speech Processing",
        "status": "running",
        "features": {
            "stt": getattr(stt_engine, 'is_initialized', False),
            "tts": getattr(tts_engine, 'is_initialized', False),
            "llm": getattr(conversation_manager, 'is_initialized', False),
            "vad": getattr(vad_detector, 'is_initialized', False)
        },
        "endpoints": {
            "health": "/health",
            "sessions": "/sessions",
            "websocket": "/ws/{session_id}",
            "test_interface": "/test"
        }
    }


@app.get("/health", response_model=HealthCheckResult)
async def health_check():
    """Enhanced health check with Phase 2 components"""
    try:
        components = {
            "session_manager": getattr(session_manager, 'is_initialized', False),
            "vad_detector": getattr(vad_detector, 'is_initialized', False),
            "stt_engine": getattr(stt_engine, 'is_initialized', False),
            "tts_engine": getattr(tts_engine, 'is_initialized', False),
            "conversation_manager": getattr(conversation_manager, 'is_initialized', False)
        }
        healthy_components = sum(components.values())
        total_components = len(components)
        health_percentage = (healthy_components / total_components) * 100
        overall_status = "healthy" if health_percentage >= 80 else "degraded" if health_percentage >= 50 else "unhealthy"
        return HealthCheckResult(
            status=overall_status,
            timestamp=time.time(),
            version="2.0.0",
            components=components,
            active_sessions=len(session_manager.sessions),
            memory_usage=None,
            performance={}
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthCheckResult(
            status="error",
            timestamp=time.time(),
            version="2.0.0",
            error=str(e)
        )


@app.post("/sessions", response_model=ConversationSession)
async def create_session(user_id: Optional[str] = None):
    """Create a new conversation session"""
    try:
        session = await session_manager.create_session(user_id)
        logger.info(f"Created session: {session.session_id}")
        return session
    except Exception as e:
        logger.error(f"Session creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sessions/{session_id}", response_model=ConversationSession)
async def get_session(session_id: str):
    """Get session information"""
    session = await session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a conversation session"""
    success = await session_manager.end_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    logger.info(f"Deleted session: {session_id}")
    return {"status": "deleted", "session_id": session_id}


@app.get("/stats")
async def get_service_stats():
    """Get comprehensive service statistics"""
    try:
        stats = {
            "service": {
                "version": "2.0.0",
                "uptime": time.time() - (getattr(app.state, 'start_time', time.time())),
                "active_sessions": len(session_manager.sessions)
            },
            "components": {
                "stt": stt_engine.get_performance_stats() if stt_engine.is_initialized else {"status": "disabled"},
                "tts": tts_engine.get_performance_stats() if tts_engine.is_initialized else {"status": "disabled"},
                "llm": conversation_manager.get_performance_stats() if conversation_manager.is_initialized else {"status": "disabled"}
            },
            "sessions": session_manager.get_stats()
        }
        return stats
    except Exception as e:
        logger.error(f"Stats retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """Enhanced WebSocket endpoint for real-time conversation"""
    correlation_id = str(uuid.uuid4())
    
    try:
        await websocket.accept()
        logger.info(f"WebSocket connected: {session_id} (correlation: {correlation_id})")
        
        # Get or create session
        session = await session_manager.get_session(session_id)
        if not session:
            await websocket.send_text(json.dumps({
                "type": "error",
                "error": "Session not found",
                "correlation_id": correlation_id
            }))
            await websocket.close()
            return
        
        # Register WebSocket connection
        await session_manager.register_websocket(session_id, websocket)
        
        # Send welcome message
        await websocket.send_text(json.dumps({
            "type": "status",
            "status": "connected",
            "session_id": session_id,
            "features": {
                "stt": stt_engine.is_initialized,
                "tts": tts_engine.is_initialized,
                "llm": conversation_manager.is_initialized
            },
            "correlation_id": correlation_id
        }))
        
        # Message processing loop
        while True:
            try:
                # Receive message
                raw_message = await websocket.receive_text()
                message_data = json.loads(raw_message)
                
                # Validate message
                validation_result = validate_message(message_data)
                if not validation_result.is_valid:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "error": f"Invalid message: {validation_result.error}",
                        "correlation_id": correlation_id
                    }))
                    continue
                
                # Process message based on type
                await process_websocket_message(websocket, session, message_data, correlation_id)
                
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "error": "Invalid JSON format",
                    "correlation_id": correlation_id
                }))
            except Exception as e:
                logger.error(f"WebSocket message processing error: {e}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "error": str(e),
                    "correlation_id": correlation_id
                }))
        
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        # Cleanup
        await session_manager.unregister_websocket(session_id)
        logger.info(f"WebSocket disconnected: {session_id}")


async def process_websocket_message(websocket: WebSocket, session: ConversationSession, 
                                  message_data: dict, correlation_id: str):
    """Process different types of WebSocket messages"""
    message_type = message_data.get("type")
    
    if message_type == "ping":
        await websocket.send_text(json.dumps({
            "type": "pong",
            "timestamp": time.time(),
            "correlation_id": correlation_id
        }))
    
    elif message_type == "audio_data":
        await process_audio_message(websocket, session, message_data, correlation_id)
    
    elif message_type == "text_message":
        await process_text_message(websocket, session, message_data, correlation_id)
    
    elif message_type == "tts_request":
        await process_tts_request(websocket, session, message_data, correlation_id)
    
    else:
        await websocket.send_text(json.dumps({
            "type": "error",
            "error": f"Unknown message type: {message_type}",
            "correlation_id": correlation_id
        }))


async def process_audio_message(websocket: WebSocket, session: ConversationSession, 
                              message_data: dict, correlation_id: str):
    """Process audio data for STT"""
    if not stt_engine.is_initialized:
        await websocket.send_text(json.dumps({
            "type": "error",
            "error": "STT engine not available",
            "correlation_id": correlation_id
        }))
        return
    
    try:
        # Decode audio data
        audio_b64 = message_data.get("audio_data", "")
        audio_bytes = base64.b64decode(audio_b64)
        
        # Create audio chunk
        audio_chunk = AudioChunk(
            session_id=session.session_id,
            data=audio_bytes,
            timestamp=time.time(),
            sample_rate=message_data.get("sample_rate", 16000),
            channels=message_data.get("channels", 1)
        )
        
        # Transcribe audio
        transcription = await stt_engine.transcribe_audio(audio_chunk)
        
        if transcription and transcription.text.strip():
            # Send transcription result
            await websocket.send_text(json.dumps({
                "type": "transcription",
                "text": transcription.text,
                "confidence": transcription.confidence,
                "language": transcription.language,
                "correlation_id": correlation_id
            }))
            
            # Generate AI response if LLM is available
            if conversation_manager.is_initialized:
                ai_response = await conversation_manager.process_user_message(session, transcription)
                
                if ai_response:
                    # Send AI response
                    await websocket.send_text(json.dumps({
                        "type": "ai_response",
                        "text": ai_response.content,
                        "correlation_id": correlation_id
                    }))
                    
                    # Generate TTS if available
                    if tts_engine.is_initialized:
                        await generate_tts_response(websocket, session, ai_response.content, correlation_id)
    
    except Exception as e:
        logger.error(f"Audio processing error: {e}")
        await websocket.send_text(json.dumps({
            "type": "error",
            "error": f"Audio processing failed: {str(e)}",
            "correlation_id": correlation_id
        }))


async def process_text_message(websocket: WebSocket, session: ConversationSession, 
                             message_data: dict, correlation_id: str):
    """Process text message (bypass STT)"""
    if not conversation_manager.is_initialized:
        await websocket.send_text(json.dumps({
            "type": "error",
            "error": "Conversation manager not available",
            "correlation_id": correlation_id
        }))
        return
    
    try:
        text = message_data.get("text", "").strip()
        if not text:
            return
        
        # Create mock transcription for consistency
        from .models import TranscriptionResult
        transcription = TranscriptionResult(
            session_id=session.session_id,
            text=text,
            confidence=1.0,
            start_time=time.time(),
            end_time=time.time(),
            is_final=True
        )
        
        # Generate AI response
        ai_response = await conversation_manager.process_user_message(session, transcription)
        
        if ai_response:
            await websocket.send_text(json.dumps({
                "type": "ai_response",
                "text": ai_response.content,
                "correlation_id": correlation_id
            }))
            
            # Generate TTS if available
            if tts_engine.is_initialized:
                await generate_tts_response(websocket, session, ai_response.content, correlation_id)
    
    except Exception as e:
        logger.error(f"Text processing error: {e}")
        await websocket.send_text(json.dumps({
            "type": "error",
            "error": f"Text processing failed: {str(e)}",
            "correlation_id": correlation_id
        }))


async def process_tts_request(websocket: WebSocket, session: ConversationSession, 
                            message_data: dict, correlation_id: str):
    """Process TTS request"""
    if not tts_engine.is_initialized:
        await websocket.send_text(json.dumps({
            "type": "error",
            "error": "TTS engine not available",
            "correlation_id": correlation_id
        }))
        return
    
    try:
        text = message_data.get("text", "").strip()
        if not text:
            return
        
        await generate_tts_response(websocket, session, text, correlation_id)
    
    except Exception as e:
        logger.error(f"TTS processing error: {e}")
        await websocket.send_text(json.dumps({
            "type": "error",
            "error": f"TTS processing failed: {str(e)}",
            "correlation_id": correlation_id
        }))


async def generate_tts_response(websocket: WebSocket, session: ConversationSession, 
                              text: str, correlation_id: str):
    """Generate TTS audio for text"""
    try:
        tts_request = TTSRequest(
            session_id=session.session_id,
            text=text,
            language="nl",
            speed=1.0
        )
        
        tts_result = await tts_engine.synthesize_speech(tts_request)
        
        if tts_result:
            # Encode audio as base64
            audio_b64 = base64.b64encode(tts_result.audio_data).decode('utf-8')
            
            await websocket.send_text(json.dumps({
                "type": "audio_response",
                "audio_data": audio_b64,
                "sample_rate": tts_result.sample_rate,
                "duration": tts_result.duration,
                "text": text,
                "correlation_id": correlation_id
            }))
    
    except Exception as e:
        logger.error(f"TTS generation error: {e}")


@app.get("/test", response_class=HTMLResponse)
async def test_interface():
    """Enhanced test interface for Phase 2"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Phase 2 Voice AI Test Interface</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
            .connected { background-color: #d4edda; color: #155724; }
            .disconnected { background-color: #f8d7da; color: #721c24; }
            .message { margin: 5px 0; padding: 5px; background-color: #f8f9fa; border-radius: 3px; }
            .user { background-color: #e3f2fd; }
            .ai { background-color: #e8f5e8; }
            .error { background-color: #ffebee; color: #c62828; }
            button { padding: 10px 15px; margin: 5px; cursor: pointer; }
            button:disabled { opacity: 0.6; cursor: not-allowed; }
            textarea { width: 100%; height: 100px; margin: 10px 0; }
            #messages { height: 300px; overflow-y: auto; border: 1px solid #ddd; padding: 10px; }
        </style>
    </head>
    <body>
        <h1>🎙️ Phase 2 Voice AI Test Interface</h1>
        
        <div id="status" class="status disconnected">Disconnected</div>
        
        <div>
            <button id="connectBtn" onclick="connect()">Connect</button>
            <button id="disconnectBtn" onclick="disconnect()" disabled>Disconnect</button>
            <button id="createSessionBtn" onclick="createSession()">New Session</button>
        </div>
        
        <div>
            <h3>Features Available:</h3>
            <div id="features">Loading...</div>
        </div>
        
        <div>
            <h3>Text Chat:</h3>
            <textarea id="textInput" placeholder="Type your message here..."></textarea>
            <button onclick="sendTextMessage()">Send Text</button>
        </div>
        
        <div>
            <h3>Audio Recording:</h3>
            <button id="recordBtn" onclick="toggleRecording()">Start Recording</button>
            <button onclick="requestTTS()">Test TTS</button>
        </div>
        
        <div>
            <h3>Conversation:</h3>
            <div id="messages"></div>
        </div>
        
        <script>
            let ws = null;
            let sessionId = null;
            let mediaRecorder = null;
            let isRecording = false;
            
            async function createSession() {
                try {
                    const response = await fetch('/sessions', { method: 'POST' });
                    const session = await response.json();
                    sessionId = session.session_id;
                    addMessage('system', `Session created: ${sessionId}`);
                } catch (error) {
                    addMessage('error', `Session creation failed: ${error.message}`);
                }
            }
            
            function connect() {
                if (!sessionId) {
                    alert('Create a session first');
                    return;
                }
                
                ws = new WebSocket(`ws://localhost:8081/ws/${sessionId}`);
                
                ws.onopen = function(event) {
                    document.getElementById('status').textContent = 'Connected';
                    document.getElementById('status').className = 'status connected';
                    document.getElementById('connectBtn').disabled = true;
                    document.getElementById('disconnectBtn').disabled = false;
                    addMessage('system', 'Connected to voice AI');
                };
                
                ws.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    handleMessage(data);
                };
                
                ws.onclose = function(event) {
                    document.getElementById('status').textContent = 'Disconnected';
                    document.getElementById('status').className = 'status disconnected';
                    document.getElementById('connectBtn').disabled = false;
                    document.getElementById('disconnectBtn').disabled = true;
                    addMessage('system', 'Disconnected from voice AI');
                };
                
                ws.onerror = function(error) {
                    addMessage('error', `WebSocket error: ${error}`);
                };
            }
            
            function disconnect() {
                if (ws) {
                    ws.close();
                    ws = null;
                }
            }
            
            function handleMessage(data) {
                switch (data.type) {
                    case 'status':
                        if (data.features) {
                            updateFeatures(data.features);
                        }
                        addMessage('system', `Status: ${data.status}`);
                        break;
                    case 'transcription':
                        addMessage('transcription', `Heard: "${data.text}" (confidence: ${data.confidence.toFixed(2)})`);
                        break;
                    case 'ai_response':
                        addMessage('ai', data.text);
                        break;
                    case 'audio_response':
                        addMessage('system', 'Audio response received');
                        playAudio(data.audio_data, data.sample_rate);
                        break;
                    case 'error':
                        addMessage('error', data.error);
                        break;
                    case 'pong':
                        addMessage('system', 'Pong received');
                        break;
                }
            }
            
            function updateFeatures(features) {
                const featuresDiv = document.getElementById('features');
                featuresDiv.innerHTML = `
                    STT (Speech-to-Text): ${features.stt ? '✅' : '❌'}<br>
                    TTS (Text-to-Speech): ${features.tts ? '✅' : '❌'}<br>
                    LLM (AI Conversation): ${features.llm ? '✅' : '❌'}
                `;
            }
            
            function sendTextMessage() {
                const input = document.getElementById('textInput');
                const text = input.value.trim();
                if (!text || !ws) return;
                
                ws.send(JSON.stringify({
                    type: 'text_message',
                    text: text
                }));
                
                addMessage('user', text);
                input.value = '';
            }
            
            function requestTTS() {
                if (!ws) return;
                
                ws.send(JSON.stringify({
                    type: 'tts_request',
                    text: 'Hallo, dit is een test van de tekst-naar-spraak functionaliteit.'
                }));
            }
            
            async function toggleRecording() {
                if (!isRecording) {
                    await startRecording();
                } else {
                    stopRecording();
                }
            }
            
            async function startRecording() {
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                    mediaRecorder = new MediaRecorder(stream);
                    
                    mediaRecorder.ondataavailable = function(event) {
                        if (event.data.size > 0 && ws) {
                            const reader = new FileReader();
                            reader.onload = function() {
                                const arrayBuffer = reader.result;
                                const uint8Array = new Uint8Array(arrayBuffer);
                                const base64 = btoa(String.fromCharCode.apply(null, uint8Array));
                                
                                ws.send(JSON.stringify({
                                    type: 'audio_data',
                                    audio_data: base64,
                                    sample_rate: 16000,
                                    channels: 1
                                }));
                            };
                            reader.readAsArrayBuffer(event.data);
                        }
                    };
                    
                    mediaRecorder.start(1000); // Record in 1-second chunks
                    isRecording = true;
                    document.getElementById('recordBtn').textContent = 'Stop Recording';
                    addMessage('system', 'Recording started');
                } catch (error) {
                    addMessage('error', `Recording failed: ${error.message}`);
                }
            }
            
            function stopRecording() {
                if (mediaRecorder) {
                    mediaRecorder.stop();
                    mediaRecorder.stream.getTracks().forEach(track => track.stop());
                    mediaRecorder = null;
                }
                isRecording = false;
                document.getElementById('recordBtn').textContent = 'Start Recording';
                addMessage('system', 'Recording stopped');
            }
            
            function playAudio(base64Data, sampleRate) {
                try {
                    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
                    const binaryString = atob(base64Data);
                    const bytes = new Uint8Array(binaryString.length);
                    for (let i = 0; i < binaryString.length; i++) {
                        bytes[i] = binaryString.charCodeAt(i);
                    }
                    
                    // Simple playback - would need proper audio decoding for production
                    addMessage('system', 'Audio playback attempted (basic implementation)');
                } catch (error) {
                    addMessage('error', `Audio playback failed: ${error.message}`);
                }
            }
            
            function addMessage(type, content) {
                const messages = document.getElementById('messages');
                const div = document.createElement('div');
                div.className = `message ${type}`;
                div.textContent = `[${new Date().toLocaleTimeString()}] ${content}`;
                messages.appendChild(div);
                messages.scrollTop = messages.scrollHeight;
            }
            
            // Auto-create session on load
            window.onload = function() {
                createSession();
            };
            
            // Allow Enter key to send text
            document.getElementById('textInput').addEventListener('keypress', function(e) {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendTextMessage();
                }
            });
        </script>
    </body>
    </html>
    """


if __name__ == "__main__":
    # Store start time for uptime calculation
    app.state.start_time = time.time()
    
    uvicorn.run(
        "main_phase2_enhanced:app",
        host=settings.service.host,
        port=8081,  # Different port for Phase 2
        reload=settings.service.debug,
        log_level=settings.service.log_level.lower()
    )
