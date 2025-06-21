"""
WebSocket handlers for real-time communication
"""
import json
import logging
import time
import base64
from typing import Dict, Any

from fastapi import WebSocket, WebSocketDisconnect

from ..models.models import ConversationSession, AudioChunk
from ..services.initialization import audio_pipeline, active_sessions
from ..core.session.manager import session_manager

logger = logging.getLogger(__name__)

async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time communication"""
    await websocket.accept()
    
    # Get or create session
    session = session_manager.get_session(session_id)
    if not session:
        session = session_manager.create_session(session_id)
    
    # Add to active sessions
    if session_id not in active_sessions:
        active_sessions[session_id] = {
            "websocket": websocket,
            "last_activity": time.time()
        }
    
    # Send welcome message
    await websocket.send_json({
        "type": "connection_established",
        "session_id": session_id,
        "message": "Connected to Voice AI Service"
    })
    
    try:
        while True:
            # Receive message
            data = await websocket.receive()
            
            # Process different message types
            if "text" in data:
                # Text message
                message_data = json.loads(data["text"])
                await process_text_message(websocket, session, message_data)
            elif "bytes" in data:
                # Binary audio data
                audio_data = data["bytes"]
                await process_audio_message(websocket, session, audio_data)
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {session_id}")
        # Remove from active sessions
        if session_id in active_sessions:
            del active_sessions[session_id]
    
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": f"Error: {str(e)}"
            })
        except:
            pass

async def process_text_message(websocket: WebSocket, session: ConversationSession, data: Dict):
    """Process text messages from WebSocket"""
    message_type = data.get("type", "unknown")
    session_id = session.session_id
    
    if message_type == "text_message":
        text = data.get("text", "")
        logger.info(f"Received text message from {session_id}: {text[:50]}...")
        
        # Process text with audio pipeline
        async for response_chunk in audio_pipeline.process_text(session_id, text):
            await websocket.send_json({
                "type": "text_response",
                "text": response_chunk,
                "final": False
            })
        
        # Send final message
        await websocket.send_json({
            "type": "text_response",
            "text": "Response complete",
            "final": True
        })
    
    elif message_type == "ping":
        await websocket.send_json({
            "type": "pong",
            "timestamp": time.time()
        })
    
    else:
        await websocket.send_json({
            "type": "error",
            "message": f"Unknown message type: {message_type}"
        })

async def process_audio_message(websocket: WebSocket, session: ConversationSession, audio_data: bytes):
    """Process audio data from WebSocket"""
    session_id = session.session_id
    
    try:
        # Create audio chunk
        chunk = AudioChunk(
            session_id=session_id,
            audio_data=audio_data,
            sample_rate=16000,  # Default, can be overridden
            channels=1,
            timestamp=time.time()
        )
        
        # Process audio with pipeline
        result = await audio_pipeline.process_audio(chunk)
        
        if result and result.text:
            # Send transcription result
            await websocket.send_json({
                "type": "transcription",
                "text": result.text,
                "confidence": result.confidence,
                "is_final": result.is_final
            })
            
            # If final result, generate response
            if result.is_final:
                # Generate TTS response
                tts_request = await audio_pipeline.generate_response(session_id, result)
                
                # Synthesize speech
                tts_response = await audio_pipeline.synthesize_speech(tts_request)
                
                # Send audio response
                await websocket.send_json({
                    "type": "audio_response",
                    "text": tts_response.text,
                    "duration": tts_response.duration
                })
                
                # Send audio data in chunks
                chunk_size = 16000  # 1 second of audio at 16kHz
                audio_data = tts_response.audio_data
                
                for i in range(0, len(audio_data), chunk_size):
                    chunk = audio_data[i:i+chunk_size]
                    await websocket.send_bytes(chunk)
    
    except Exception as e:
        logger.error(f"Error processing audio: {str(e)}")
        await websocket.send_json({
            "type": "error",
            "message": f"Error processing audio: {str(e)}"
        })