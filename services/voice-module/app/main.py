"""
Voice Module Service - Main Application

This is the main FastAPI application for the Voice Module service.
It handles real-time voice processing, speech-to-text, text-to-speech,
and WebRTC communication.
"""

import logging
import asyncio
from contextlib import asynccontextmanager
from typing import Dict, Any
from fastapi import FastAPI, WebSocket, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse

from .core.config import settings
from .core.voice_processor import VoiceProcessor
from .core.websocket_manager import WebSocketManager
from .api.routes import voice_processing, health, websocket_routes
from .middleware.logging import setup_logging
from .middleware.metrics import add_prometheus_metrics

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    logger.info("Starting Voice Module Service...")
    
    # Initialize Voice Processor
    voice_processor = VoiceProcessor()
    await voice_processor.initialize()
    app.state.voice_processor = voice_processor
    
    # Initialize WebSocket Manager
    websocket_manager = WebSocketManager()
    app.state.websocket_manager = websocket_manager
    
    logger.info("Voice Module Service started successfully")
    yield
    
    # Cleanup
    logger.info("Shutting down Voice Module Service...")
    await voice_processor.cleanup()
    await websocket_manager.cleanup()
    logger.info("Voice Module Service stopped")


# Create FastAPI application
app = FastAPI(
    title="Voice Module Service",
    description="Real-time voice processing and communication service for AI Voice Agent platform",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for voice interface
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Add Prometheus metrics if enabled
if settings.ENABLE_METRICS:
    add_prometheus_metrics(app)

# Include routers
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(voice_processing.router, prefix="/api/v1/voice", tags=["Voice Processing"])
app.include_router(websocket_routes.router, prefix="/ws", tags=["WebSocket"])


@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "Voice Module Service",
        "version": "1.0.0",
        "description": "Real-time voice processing and communication service",
        "status": "operational",
        "capabilities": [
            "Speech-to-Text (Whisper)",
            "Text-to-Speech (TTS)",
            "Real-time WebRTC streaming",
            "Voice Activity Detection",
            "Multi-language support",
            "Audio preprocessing"
        ],
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "voice_processing": "/api/v1/voice",
            "websocket": "/ws",
            "voice_interface": "/voice"
        }
    }


@app.get("/voice", response_class=HTMLResponse)
async def voice_interface():
    """Voice interface for testing and demonstration."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI Voice Agent - Voice Interface</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                min-height: 100vh;
            }
            .container {
                background: rgba(255, 255, 255, 0.1);
                border-radius: 15px;
                padding: 30px;
                backdrop-filter: blur(10px);
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            }
            h1 {
                text-align: center;
                margin-bottom: 30px;
                font-size: 2.5em;
            }
            .controls {
                display: flex;
                justify-content: center;
                gap: 20px;
                margin: 30px 0;
            }
            button {
                padding: 15px 30px;
                font-size: 18px;
                border: none;
                border-radius: 25px;
                cursor: pointer;
                transition: all 0.3s ease;
                font-weight: bold;
            }
            .record-btn {
                background: #ff4757;
                color: white;
            }
            .record-btn:hover {
                background: #ff3838;
                transform: translateY(-2px);
            }
            .record-btn.recording {
                background: #ff6b7a;
                animation: pulse 2s infinite;
            }
            @keyframes pulse {
                0% { transform: scale(1); }
                50% { transform: scale(1.05); }
                100% { transform: scale(1); }
            }
            .status {
                text-align: center;
                margin: 20px 0;
                font-size: 18px;
                min-height: 50px;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .transcript {
                background: rgba(255, 255, 255, 0.1);
                border-radius: 10px;
                padding: 20px;
                min-height: 100px;
                margin: 20px 0;
                border: 2px solid rgba(255, 255, 255, 0.2);
            }
            .response {
                background: rgba(0, 255, 150, 0.1);
                border-radius: 10px;
                padding: 20px;
                min-height: 100px;
                margin: 20px 0;
                border: 2px solid rgba(0, 255, 150, 0.3);
            }
            .error {
                background: rgba(255, 0, 0, 0.1);
                border: 2px solid rgba(255, 0, 0, 0.3);
                color: #ffcccb;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎙️ AI Voice Agent</h1>
            <div class="controls">
                <button id="recordBtn" class="record-btn">🎤 Start Recording</button>
                <button id="clearBtn" style="background: #5f27cd; color: white;">🗑️ Clear</button>
            </div>
            <div id="status" class="status">Ready to record</div>
            <div id="transcript" class="transcript">
                <strong>Transcript:</strong><br>
                <span id="transcriptText">Your speech will appear here...</span>
            </div>
            <div id="response" class="response">
                <strong>AI Response:</strong><br>
                <span id="responseText">AI responses will appear here...</span>
            </div>
        </div>

        <script>
            const recordBtn = document.getElementById('recordBtn');
            const clearBtn = document.getElementById('clearBtn');
            const status = document.getElementById('status');
            const transcriptText = document.getElementById('transcriptText');
            const responseText = document.getElementById('responseText');
            
            let isRecording = false;
            let mediaRecorder;
            let audioChunks = [];
            let websocket;
            
            // Initialize WebSocket connection
            function initWebSocket() {
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = `${protocol}//${window.location.host}/ws/voice`;
                
                websocket = new WebSocket(wsUrl);
                
                websocket.onopen = function(event) {
                    console.log('WebSocket connected');
                    status.textContent = 'Connected - Ready to record';
                };
                
                websocket.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    
                    if (data.type === 'transcript') {
                        transcriptText.textContent = data.text;
                    } else if (data.type === 'response') {
                        responseText.textContent = data.text;
                    } else if (data.type === 'error') {
                        status.textContent = 'Error: ' + data.message;
                        status.className = 'status error';
                    }
                };
                
                websocket.onclose = function(event) {
                    status.textContent = 'Disconnected - Trying to reconnect...';
                    setTimeout(initWebSocket, 3000);
                };
                
                websocket.onerror = function(error) {
                    console.error('WebSocket error:', error);
                    status.textContent = 'Connection error';
                };
            }
            
            // Start recording
            async function startRecording() {
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                    mediaRecorder = new MediaRecorder(stream);
                    audioChunks = [];
                    
                    mediaRecorder.ondataavailable = function(event) {
                        audioChunks.push(event.data);
                    };
                    
                    mediaRecorder.onstop = function() {
                        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                        sendAudioToServer(audioBlob);
                    };
                    
                    mediaRecorder.start();
                    isRecording = true;
                    recordBtn.textContent = '⏹️ Stop Recording';
                    recordBtn.classList.add('recording');
                    status.textContent = 'Recording... Speak now!';
                    
                } catch (error) {
                    console.error('Error accessing microphone:', error);
                    status.textContent = 'Error: Could not access microphone';
                    status.className = 'status error';
                }
            }
            
            // Stop recording
            function stopRecording() {
                if (mediaRecorder && isRecording) {
                    mediaRecorder.stop();
                    isRecording = false;
                    recordBtn.textContent = '🎤 Start Recording';
                    recordBtn.classList.remove('recording');
                    status.textContent = 'Processing audio...';
                    
                    // Stop all audio tracks
                    const tracks = mediaRecorder.stream.getTracks();
                    tracks.forEach(track => track.stop());
                }
            }
            
            // Send audio to server
            async function sendAudioToServer(audioBlob) {
                try {
                    const formData = new FormData();
                    formData.append('audio', audioBlob, 'recording.wav');
                    
                    const response = await fetch('/api/v1/voice/transcribe', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const result = await response.json();
                    
                    if (result.transcript) {
                        transcriptText.textContent = result.transcript;
                        
                        // Send to AI for response
                        if (websocket.readyState === WebSocket.OPEN) {
                            websocket.send(JSON.stringify({
                                type: 'message',
                                text: result.transcript
                            }));
                        }
                    }
                    
                    status.textContent = 'Ready to record';
                    status.className = 'status';
                    
                } catch (error) {
                    console.error('Error sending audio:', error);
                    status.textContent = 'Error processing audio';
                    status.className = 'status error';
                }
            }
            
            // Event listeners
            recordBtn.addEventListener('click', function() {
                if (isRecording) {
                    stopRecording();
                } else {
                    startRecording();
                }
            });
            
            clearBtn.addEventListener('click', function() {
                transcriptText.textContent = 'Your speech will appear here...';
                responseText.textContent = 'AI responses will appear here...';
                status.textContent = 'Ready to record';
                status.className = 'status';
            });
            
            // Initialize WebSocket on page load
            initWebSocket();
        </script>
    </body>
    </html>
    """


@app.get("/status")
async def get_status():
    """Get detailed service status."""
    voice_processor = getattr(app.state, 'voice_processor', None)
    websocket_manager = getattr(app.state, 'websocket_manager', None)
    
    if voice_processor:
        processor_status = await voice_processor.get_status()
    else:
        processor_status = {"status": "not_initialized"}
    
    if websocket_manager:
        ws_status = await websocket_manager.get_status()
    else:
        ws_status = {"status": "not_initialized"}
    
    return {
        "service": "voice-module",
        "status": "healthy",
        "version": "1.0.0",
        "components": {
            "voice_processor": processor_status,
            "websocket_manager": ws_status,
            "capabilities": {
                "whisper": "enabled",
                "tts": "enabled",
                "webrtc": "enabled",
                "vad": "enabled"
            }
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8001,
        reload=settings.DEBUG,
        log_level="info"
    )