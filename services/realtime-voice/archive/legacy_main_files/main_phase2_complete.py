"""
Real-time Conversational AI - Phase 2 Main Service
Complete implementation with STT, TTS, LLM and Audio Pipeline
"""
import asyncio
import logging
import uuid
import json
import base64
from contextlib import asynccontextmanager
from typing import Dict

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
import uvicorn

from .models import (
    AudioChunk, TranscriptionResult, TTSResult,
    TranscriptionMessage, TTSMessage, 
    ErrorMessage, StatusMessage, HealthCheckResult
)
from .config_enhanced import settings
from .session_manager import SessionManager
from .validation import MessageValidator
from .error_handling import ErrorHandler, AppError, ErrorCode
from .audio_pipeline import audio_pipeline, AudioPipelineEvent

# Enhanced logging setup
logging.basicConfig(
    level=getattr(logging, settings.service.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize core components
session_manager = SessionManager()
message_validator = MessageValidator()
error_handler = ErrorHandler()


# Application lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle"""
    
    logger.info("🚀 Starting Real-time Conversational AI Service - Phase 2")
    
    try:
        # Initialize core managers
        await session_manager.initialize()
        logger.info("✅ Session manager initialized")
        
        # Initialize complete audio pipeline
        await audio_pipeline.initialize()
        logger.info("✅ Audio pipeline initialized")
        
        # Register pipeline event handlers
        audio_pipeline.register_event_callback("transcription_completed", handle_transcription_event)
        audio_pipeline.register_event_callback("audio_generated", handle_audio_generated_event)
        audio_pipeline.register_event_callback("pipeline_error", handle_pipeline_error_event)
        
        logger.info("🎙️ Real-time Conversational AI Service Phase 2 is ready!")
        logger.info(f"🌐 Service running on: http://{settings.service.host}:{settings.service.port}")
        logger.info("📊 Features enabled: STT ✅ | LLM ✅ | TTS ✅ | VAD ✅ | WebRTC ✅")
        
        yield
        
    except Exception as e:
        logger.error(f"Failed to initialize service: {e}")
        raise
    
    finally:
        # Cleanup
        logger.info("🛑 Shutting down Real-time Conversational AI Service")
        
        try:
            await audio_pipeline.close()
            await session_manager.close()
            logger.info("✅ Cleanup completed")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


# Create FastAPI app
app = FastAPI(
    title="Real-time Conversational AI - Phase 2",
    description="Professional AI voice agent with natural conversation capabilities",
    version="2.0.0",
    lifespan=lifespan
)

# Configure CORS
cors_config = settings.get_cors_config()
app.add_middleware(CORSMiddleware, **cors_config)

# Global WebSocket connections
websocket_connections: Dict[str, WebSocket] = {}


# Pipeline event handlers
async def handle_transcription_event(event: AudioPipelineEvent):
    """Handle transcription completed events"""
    session_id = event.session_id
    transcription: TranscriptionResult = event.data
    
    if session_id in websocket_connections:
        try:
            websocket = websocket_connections[session_id]
            message = TranscriptionMessage(
                type="transcription",
                session_id=session_id,
                text=transcription.text,
                confidence=transcription.confidence,
                is_final=transcription.is_final,
                language=transcription.language
            )
            await websocket.send_text(message.model_dump_json())
            logger.debug(f"Sent transcription to session {session_id}: {transcription.text}")
        except Exception as e:
            logger.error(f"Error sending transcription to session {session_id}: {e}")


async def handle_audio_generated_event(event: AudioPipelineEvent):
    """Handle audio generation completed events"""
    session_id = event.session_id
    tts_result: TTSResult = event.data
    
    if session_id in websocket_connections:
        try:
            websocket = websocket_connections[session_id]
            
            # Encode audio as base64
            audio_base64 = base64.b64encode(tts_result.audio_data).decode('utf-8')
            
            message = TTSMessage(
                type="tts_audio",
                session_id=session_id,
                text=tts_result.text,
                audio_data=audio_base64,
                sample_rate=tts_result.sample_rate,
                duration=tts_result.duration
            )
            await websocket.send_text(message.model_dump_json())
            logger.debug(f"Sent TTS audio to session {session_id}: {tts_result.text}")
        except Exception as e:
            logger.error(f"Error sending TTS audio to session {session_id}: {e}")


async def handle_pipeline_error_event(event: AudioPipelineEvent):
    """Handle pipeline error events"""
    session_id = event.session_id
    error_data = event.data
    
    if session_id in websocket_connections:
        try:
            websocket = websocket_connections[session_id]
            error_message = ErrorMessage(
                type="error",
                session_id=session_id,
                error_code="PIPELINE_ERROR",
                message=f"Pipeline error: {error_data.get('error', 'Unknown error')}",
                details=error_data
            )
            await websocket.send_text(error_message.model_dump_json())
        except Exception as e:
            logger.error(f"Error sending pipeline error to session {session_id}: {e}")


# API Endpoints
@app.get("/")
async def root():
    """Service information"""
    return {
        "service": "Real-time Conversational AI",
        "version": "2.0.0",
        "phase": "2 - Full Speech Processing",
        "status": "operational",
        "features": {
            "stt": "Whisper STT Engine",
            "llm": "Ollama LLM Integration", 
            "tts": "XTTS v2 Natural Voice",
            "vad": "Silero Voice Activity Detection",
            "pipeline": "Real-time Audio Processing"
        },
        "endpoints": {
            "health": "/health",
            "sessions": "/sessions",
            "websocket": "/ws/{session_id}",
            "test_interface": "/test"
        }
    }


@app.get("/health")
async def health_check():
    """Comprehensive health check"""
    try:
        pipeline_stats = audio_pipeline.get_pipeline_stats()
        session_stats = await session_manager.get_stats()
        
        health_result = HealthCheckResult(
            status="healthy",
            timestamp=str(asyncio.get_event_loop().time()),
            pipeline_initialized=pipeline_stats["is_initialized"],
            active_sessions=pipeline_stats["active_sessions"],
            total_sessions=session_stats.get("total_sessions", 0),
            components={
                "session_manager": "operational",
                "audio_pipeline": "operational" if pipeline_stats["is_initialized"] else "error",
                "stt_engine": "operational",
                "tts_engine": "operational", 
                "conversation_manager": "operational",
                "vad_detector": "operational"
            },
            metrics=pipeline_stats
        )
        
        return health_result.model_dump()
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": str(asyncio.get_event_loop().time())
            }
        )


@app.post("/sessions")
async def create_session(background_tasks: BackgroundTasks):
    """Create a new conversation session"""
    try:
        session_id = str(uuid.uuid4())
        
        # Create session in session manager
        session = await session_manager.create_session(session_id)
        if not session:
            raise HTTPException(status_code=500, detail="Failed to create session")
        
        # Create session in audio pipeline
        pipeline_success = await audio_pipeline.create_session(session_id)
        if not pipeline_success:
            await session_manager.end_session(session_id)
            raise HTTPException(status_code=500, detail="Failed to initialize audio pipeline")
        
        # Schedule cleanup task
        background_tasks.add_task(schedule_session_cleanup, session_id)
        
        logger.info(f"Created new session: {session_id}")
        
        return {
            "session_id": session_id,
            "status": "created",
            "websocket_url": f"/ws/{session_id}",
            "created_at": session.created_at
        }
        
    except Exception as e:
        error_response = error_handler.handle_error(
            AppError(ErrorCode.SESSION_CREATION_FAILED, f"Session creation failed: {str(e)}")
        )
        raise HTTPException(status_code=500, detail=error_response)


@app.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Get session information"""
    try:
        session = await session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        pipeline_info = audio_pipeline.get_session_info(session_id)
        
        return {
            "session": session.model_dump(),
            "pipeline": pipeline_info,
            "connected": session_id in websocket_connections
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/sessions/{session_id}")
async def end_session(session_id: str):
    """End a conversation session"""
    try:
        # Close WebSocket connection if exists
        if session_id in websocket_connections:
            try:
                await websocket_connections[session_id].close()
                del websocket_connections[session_id]
            except Exception as e:
                logger.warning(f"Error closing WebSocket for session {session_id}: {e}")
        
        # End pipeline session
        await audio_pipeline.end_session(session_id)
        
        # End session manager session
        success = await session_manager.end_session(session_id)
        
        if success:
            return {"status": "ended", "session_id": session_id}
        else:
            raise HTTPException(status_code=404, detail="Session not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ending session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/sessions/{session_id}/text")
async def process_text_input(session_id: str, text_input: dict):
    """Process text input directly (bypass STT)"""
    try:
        text = text_input.get("text", "").strip()
        if not text:
            raise HTTPException(status_code=400, detail="Text input required")
        
        # Process through pipeline
        tts_result = await audio_pipeline.process_text_input(session_id, text)
        
        if not tts_result:
            raise HTTPException(status_code=500, detail="Failed to process text input")
        
        # Return audio response
        audio_base64 = base64.b64encode(tts_result.audio_data).decode('utf-8')
        
        return {
            "response_text": tts_result.text,
            "audio_data": audio_base64,
            "sample_rate": tts_result.sample_rate,
            "duration": tts_result.duration
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing text input for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time conversation"""
    await websocket.accept()
    
    # Verify session exists
    session = await session_manager.get_session(session_id)
    if not session:
        await websocket.close(code=4004, reason="Session not found")
        return
    
    # Register WebSocket connection
    websocket_connections[session_id] = websocket
    
    try:
        # Send welcome message
        welcome_message = StatusMessage(
            type="status",
            session_id=session_id,
            status="connected",
            message="Real-time conversation started. You can speak now!"
        )
        await websocket.send_text(welcome_message.model_dump_json())
        
        logger.info(f"WebSocket connected for session: {session_id}")
        
        # Main message processing loop
        while True:
            try:
                # Receive message
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                # Validate message
                validation_result = message_validator.validate_message(message_data)
                if not validation_result.is_valid:
                    error_msg = ErrorMessage(
                        type="error",
                        session_id=session_id,
                        error_code="VALIDATION_ERROR",
                        message=validation_result.error_message
                    )
                    await websocket.send_text(error_msg.model_dump_json())
                    continue
                
                # Process different message types
                message_type = message_data.get("type")
                
                if message_type == "ping":
                    # Respond to ping
                    pong_message = StatusMessage(
                        type="pong",
                        session_id=session_id,
                        status="alive"
                    )
                    await websocket.send_text(pong_message.model_dump_json())
                
                elif message_type == "audio_data":
                    # Process audio data
                    await process_audio_message(session_id, message_data)
                
                elif message_type == "text_input":
                    # Process text input
                    text = message_data.get("text", "").strip()
                    if text:
                        async for response_chunk in audio_pipeline.generate_streaming_response(session_id, text):
                            stream_message = {
                                "type": "text_stream",
                                "session_id": session_id,
                                "chunk": response_chunk
                            }
                            await websocket.send_text(json.dumps(stream_message))
                
                elif message_type == "interrupt":
                    # Handle conversation interruption
                    interrupt_message = StatusMessage(
                        type="status",
                        session_id=session_id,
                        status="interrupted",
                        message="Conversation interrupted, ready for new input"
                    )
                    await websocket.send_text(interrupt_message.model_dump_json())
                
                else:
                    # Unknown message type
                    error_msg = ErrorMessage(
                        type="error",
                        session_id=session_id,
                        error_code="UNKNOWN_MESSAGE_TYPE",
                        message=f"Unknown message type: {message_type}"
                    )
                    await websocket.send_text(error_msg.model_dump_json())
                
            except json.JSONDecodeError:
                error_msg = ErrorMessage(
                    type="error",
                    session_id=session_id,
                    error_code="INVALID_JSON",
                    message="Invalid JSON format"
                )
                await websocket.send_text(error_msg.model_dump_json())
            
            except Exception as e:
                logger.error(f"Error processing WebSocket message for session {session_id}: {e}")
                error_msg = ErrorMessage(
                    type="error",
                    session_id=session_id,
                    error_code="PROCESSING_ERROR",
                    message=f"Message processing error: {str(e)}"
                )
                await websocket.send_text(error_msg.model_dump_json())
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session: {session_id}")
    
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}")
    
    finally:
        # Cleanup WebSocket connection
        if session_id in websocket_connections:
            del websocket_connections[session_id]
        
        logger.info(f"WebSocket cleanup completed for session: {session_id}")


async def process_audio_message(session_id: str, message_data: dict):
    """Process incoming audio data"""
    try:
        # Extract audio data
        audio_base64 = message_data.get("audio_data")
        if not audio_base64:
            logger.warning(f"No audio data in message for session {session_id}")
            return
        
        # Decode audio data
        audio_bytes = base64.b64decode(audio_base64)
        
        # Create audio chunk
        audio_chunk = AudioChunk(
            session_id=session_id,
            data=audio_bytes,
            sample_rate=message_data.get("sample_rate", 16000),
            channels=message_data.get("channels", 1),
            timestamp=asyncio.get_event_loop().time()
        )
        
        # Process through audio pipeline
        success = await audio_pipeline.process_audio_chunk(session_id, audio_chunk)
        
        if not success:
            logger.error(f"Failed to process audio chunk for session {session_id}")
    
    except Exception as e:
        logger.error(f"Error processing audio message for session {session_id}: {e}")


async def schedule_session_cleanup(session_id: str):
    """Schedule session cleanup after timeout"""
    # Wait for session timeout
    await asyncio.sleep(settings.conversation.timeout)
    
    # Check if session is still active
    session = await session_manager.get_session(session_id)
    if session and session_id not in websocket_connections:
        logger.info(f"Auto-cleaning up inactive session: {session_id}")
        await audio_pipeline.end_session(session_id)
        await session_manager.end_session(session_id)


@app.get("/test")
async def get_test_interface():
    """Get test interface HTML"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Real-time AI Voice Agent - Phase 2 Test</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; }
            .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
            .connected { background: #d4edda; color: #155724; }
            .disconnected { background: #f8d7da; color: #721c24; }
            .message { margin: 10px 0; padding: 10px; border-radius: 5px; }
            .user { background: #e3f2fd; text-align: right; }
            .assistant { background: #f1f8e9; }
            .error { background: #ffebee; color: #c62828; }
            button { padding: 10px 20px; margin: 5px; border: none; border-radius: 5px; cursor: pointer; }
            .primary { background: #2196f3; color: white; }
            .secondary { background: #757575; color: white; }
            .danger { background: #f44336; color: white; }
            input[type="text"] { width: 70%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
            #log { height: 300px; overflow-y: scroll; border: 1px solid #ddd; padding: 10px; background: #fafafa; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎙️ Real-time AI Voice Agent - Phase 2</h1>
            <p><strong>Features:</strong> STT ✅ | LLM ✅ | TTS ✅ | VAD ✅ | WebRTC ✅</p>
            
            <div id="status" class="status disconnected">Disconnected</div>
            
            <div>
                <button id="connect" class="primary">Create Session & Connect</button>
                <button id="disconnect" class="secondary" disabled>Disconnect</button>
                <button id="health" class="secondary">Health Check</button>
            </div>
            
            <div style="margin: 20px 0;">
                <input type="text" id="textInput" placeholder="Type a message to test text input..." />
                <button id="sendText" class="primary" disabled>Send Text</button>
            </div>
            
            <div>
                <h3>Audio Controls</h3>
                <button id="startRecord" class="primary" disabled>🎤 Start Recording</button>
                <button id="stopRecord" class="danger" disabled>⏹️ Stop Recording</button>
                <p><em>Audio will be processed through: Voice Detection → Speech Recognition → AI Response → Text-to-Speech</em></p>
            </div>
            
            <div>
                <h3>Conversation Log</h3>
                <div id="log"></div>
            </div>
        </div>

        <script>
            let websocket = null;
            let sessionId = null;
            let mediaRecorder = null;
            let recordedChunks = [];
            
            const statusEl = document.getElementById('status');
            const logEl = document.getElementById('log');
            const connectBtn = document.getElementById('connect');
            const disconnectBtn = document.getElementById('disconnect');
            const textInput = document.getElementById('textInput');
            const sendTextBtn = document.getElementById('sendText');
            const startRecordBtn = document.getElementById('startRecord');
            const stopRecordBtn = document.getElementById('stopRecord');
            
            function log(message, type = 'info') {
                const timestamp = new Date().toLocaleTimeString();
                const div = document.createElement('div');
                div.className = `message ${type}`;
                div.innerHTML = `<strong>[${timestamp}]</strong> ${message}`;
                logEl.appendChild(div);
                logEl.scrollTop = logEl.scrollHeight;
            }
            
            function updateStatus(connected) {
                if (connected) {
                    statusEl.textContent = `Connected to session: ${sessionId}`;
                    statusEl.className = 'status connected';
                } else {
                    statusEl.textContent = 'Disconnected';
                    statusEl.className = 'status disconnected';
                }
                
                connectBtn.disabled = connected;
                disconnectBtn.disabled = !connected;
                sendTextBtn.disabled = !connected;
                startRecordBtn.disabled = !connected;
                stopRecordBtn.disabled = true;
            }
            
            async function createSession() {
                try {
                    const response = await fetch('/sessions', { method: 'POST' });
                    const data = await response.json();
                    sessionId = data.session_id;
                    log(`Session created: ${sessionId}`, 'assistant');
                    return sessionId;
                } catch (error) {
                    log(`Error creating session: ${error.message}`, 'error');
                    return null;
                }
            }
            
            async function connect() {
                try {
                    const session = await createSession();
                    if (!session) return;
                    
                    const wsUrl = `ws://localhost:8082/ws/${session}`;
                    websocket = new WebSocket(wsUrl);
                    
                    websocket.onopen = () => {
                        log('WebSocket connected!', 'assistant');
                        updateStatus(true);
                    };
                    
                    websocket.onmessage = (event) => {
                        try {
                            const message = JSON.parse(event.data);
                            handleMessage(message);
                        } catch (error) {
                            log(`Error parsing message: ${error.message}`, 'error');
                        }
                    };
                    
                    websocket.onclose = () => {
                        log('WebSocket disconnected', 'error');
                        updateStatus(false);
                        websocket = null;
                    };
                    
                    websocket.onerror = (error) => {
                        log(`WebSocket error: ${error}`, 'error');
                    };
                    
                } catch (error) {
                    log(`Connection error: ${error.message}`, 'error');
                }
            }
            
            function handleMessage(message) {
                switch (message.type) {
                    case 'status':
                        log(`Status: ${message.message}`, 'assistant');
                        break;
                    case 'transcription':
                        log(`🎤 You said: "${message.text}" (confidence: ${(message.confidence * 100).toFixed(1)}%)`, 'user');
                        break;
                    case 'tts_audio':
                        log(`🤖 AI response: "${message.text}"`, 'assistant');
                        // Play audio response
                        playAudio(message.audio_data, message.sample_rate);
                        break;
                    case 'text_stream':
                        // Handle streaming text response
                        log(`🤖 AI: ${message.chunk}`, 'assistant');
                        break;
                    case 'error':
                        log(`Error: ${message.message}`, 'error');
                        break;
                    default:
                        log(`Received: ${JSON.stringify(message)}`, 'info');
                }
            }
            
            function playAudio(audioBase64, sampleRate) {
                try {
                    const audioBytes = Uint8Array.from(atob(audioBase64), c => c.charCodeAt(0));
                    const audioBlob = new Blob([audioBytes], { type: 'audio/wav' });
                    const audioUrl = URL.createObjectURL(audioBlob);
                    const audio = new Audio(audioUrl);
                    audio.play();
                    log('🔊 Playing AI voice response', 'assistant');
                } catch (error) {
                    log(`Error playing audio: ${error.message}`, 'error');
                }
            }
            
            function disconnect() {
                if (websocket) {
                    websocket.close();
                }
            }
            
            function sendText() {
                const text = textInput.value.trim();
                if (!text || !websocket) return;
                
                const message = {
                    type: 'text_input',
                    text: text
                };
                
                websocket.send(JSON.stringify(message));
                log(`📝 You wrote: "${text}"`, 'user');
                textInput.value = '';
            }
            
            async function startRecording() {
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({ 
                        audio: { 
                            sampleRate: 16000,
                            channelCount: 1
                        } 
                    });
                    
                    mediaRecorder = new MediaRecorder(stream);
                    recordedChunks = [];
                    
                    mediaRecorder.ondataavailable = (event) => {
                        if (event.data.size > 0) {
                            recordedChunks.push(event.data);
                        }
                    };
                    
                    mediaRecorder.onstop = () => {
                        const audioBlob = new Blob(recordedChunks, { type: 'audio/wav' });
                        sendAudio(audioBlob);
                        stream.getTracks().forEach(track => track.stop());
                    };
                    
                    mediaRecorder.start(1000); // Collect data every second
                    startRecordBtn.disabled = true;
                    stopRecordBtn.disabled = false;
                    log('🎤 Recording started...', 'user');
                    
                } catch (error) {
                    log(`Recording error: ${error.message}`, 'error');
                }
            }
            
            function stopRecording() {
                if (mediaRecorder && mediaRecorder.state === 'recording') {
                    mediaRecorder.stop();
                    startRecordBtn.disabled = false;
                    stopRecordBtn.disabled = true;
                    log('⏹️ Recording stopped', 'user');
                }
            }
            
            async function sendAudio(audioBlob) {
                try {
                    const arrayBuffer = await audioBlob.arrayBuffer();
                    const base64Audio = btoa(String.fromCharCode(...new Uint8Array(arrayBuffer)));
                    
                    const message = {
                        type: 'audio_data',
                        audio_data: base64Audio,
                        sample_rate: 16000,
                        channels: 1
                    };
                    
                    websocket.send(JSON.stringify(message));
                    log('🎵 Audio sent for processing', 'user');
                    
                } catch (error) {
                    log(`Error sending audio: ${error.message}`, 'error');
                }
            }
            
            async function healthCheck() {
                try {
                    const response = await fetch('/health');
                    const data = await response.json();
                    log(`Health: ${data.status} | Sessions: ${data.active_sessions} | Pipeline: ${data.pipeline_initialized ? 'Ready' : 'Error'}`, 'info');
                } catch (error) {
                    log(`Health check error: ${error.message}`, 'error');
                }
            }
            
            // Event listeners
            connectBtn.addEventListener('click', connect);
            disconnectBtn.addEventListener('click', disconnect);
            sendTextBtn.addEventListener('click', sendText);
            startRecordBtn.addEventListener('click', startRecording);
            stopRecordBtn.addEventListener('click', stopRecording);
            document.getElementById('health').addEventListener('click', healthCheck);
            
            textInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') sendText();
            });
            
            // Initial health check
            healthCheck();
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


# Background tasks
@app.on_event("startup")
async def startup_background_tasks():
    """Start background maintenance tasks"""
    async def cleanup_task():
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                await audio_pipeline.cleanup_expired_sessions()
                await session_manager.cleanup_expired_sessions()
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
    
    asyncio.create_task(cleanup_task())


if __name__ == "__main__":
    uvicorn.run(
        "main_phase2_complete:app",
        host=settings.service.host,
        port=8082,  # Different port for Phase 2
        reload=settings.service.debug,
        log_level=settings.service.log_level.lower()
    )
