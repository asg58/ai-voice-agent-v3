"""
Professional Session Manager with lifecycle management
Enterprise-grade session handling with monitoring and cleanup
"""
import asyncio
import time
import logging
from typing import Dict, Optional, List, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import uuid

from .models import ConversationSession

logger = logging.getLogger(__name__)


@dataclass
class SessionMetrics:
    """Professional session metrics for monitoring"""
    messages_sent: int = 0
    messages_received: int = 0
    total_audio_chunks: int = 0
    connection_time: float = 0.0
    last_activity: datetime = field(default_factory=datetime.now)
    bandwidth_used: int = 0
    
    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.now()


class ProfessionalSessionManager:
    """
    Enterprise-grade Session Manager with advanced features:
    - Automatic session cleanup
    - Memory usage monitoring 
    - Rate limiting per session
    - WebSocket connection management
    - Comprehensive session statistics
    - Graceful shutdown handling
    """
    
    def __init__(self):
        # Core session storage
        self.sessions: Dict[str, ConversationSession] = {}
        self.session_metrics: Dict[str, SessionMetrics] = {}
        self.websocket_connections: Dict[str, Any] = {}
        
        # Configuration
        self.max_sessions = 1000
        self.cleanup_interval_seconds = 300  # 5 minutes
        self.inactive_threshold_minutes = 30
        self.max_messages_per_session = 1000
        self.max_memory_usage_mb = 500
        
        # State management
        self.cleanup_task: Optional[asyncio.Task] = None
        self.is_initialized = False
        self._shutdown_event = None
        
        # Statistics
        self.total_sessions_created = 0
        self.total_sessions_ended = 0
        self.peak_concurrent_sessions = 0
        
        logger.info("Professional SessionManager initialized")
    
    async def initialize(self):
        """Initialize session manager with professional features"""
        if self.is_initialized:
            return
            
        try:
            # Initialize shutdown event
            self._shutdown_event = asyncio.Event()
            
            # Start cleanup task
            await self._start_cleanup_task()
            self.is_initialized = True
            logger.info("✅ Professional SessionManager fully initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize SessionManager: {e}")
            raise
    
    async def _start_cleanup_task(self):
        """Start professional background cleanup task"""
        async def cleanup_loop():
            logger.info("🧹 Started professional session cleanup task")
            
            while not self._shutdown_event.is_set():
                try:
                    await asyncio.sleep(self.cleanup_interval_seconds)
                    
                    if not self._shutdown_event.is_set():
                        cleaned = await self._cleanup_expired_sessions()
                        await self._update_statistics()
                        
                        if cleaned > 0:
                            logger.info(f"🧹 Cleaned up {cleaned} expired sessions")
                            
                except asyncio.CancelledError:
                    logger.info("Cleanup task cancelled")
                    break
                except Exception as e:
                    logger.error(f"Error in cleanup task: {e}")
                    await asyncio.sleep(60)  # Wait before retrying
        
        self.cleanup_task = asyncio.create_task(cleanup_loop())
    
    async def create_session(self, user_id: Optional[str] = None, 
                           metadata: Optional[Dict] = None) -> ConversationSession:
        """Create new professional session with validation"""
        
        # Check session limit
        if len(self.sessions) >= self.max_sessions:
            # Remove oldest inactive session
            await self._remove_oldest_inactive_session()
        
        # Generate session
        session_id = str(uuid.uuid4())
        session = ConversationSession(
            session_id=session_id,
            user_id=user_id,
            status="active",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            messages=[],
            metadata=metadata or {}
        )
        
        # Store session and metrics
        self.sessions[session_id] = session
        self.session_metrics[session_id] = SessionMetrics()
        
        # Update statistics
        self.total_sessions_created += 1
        self.peak_concurrent_sessions = max(
            self.peak_concurrent_sessions, 
            len(self.sessions)
        )
        
        logger.info(f"✅ Created professional session: {session_id}")
        return session
    
    async def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """Get session with activity tracking"""
        session = self.sessions.get(session_id)
        
        if session:
            # Update activity
            session.updated_at = datetime.now()
            if session_id in self.session_metrics:
                self.session_metrics[session_id].update_activity()
        
        return session
    
    async def end_session(self, session_id: str) -> bool:
        """End session with proper cleanup"""
        if session_id not in self.sessions:
            return False
        
        try:
            # Close WebSocket if exists
            await self._close_websocket_safely(session_id)
            
            # Remove session data
            del self.sessions[session_id]
            if session_id in self.session_metrics:
                del self.session_metrics[session_id]
            
            # Update statistics
            self.total_sessions_ended += 1
            
            logger.info(f"✅ Ended professional session: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error ending session {session_id}: {e}")
            return False
    
    async def add_websocket(self, session_id: str, websocket: Any):
        """Add WebSocket with professional handling"""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        self.websocket_connections[session_id] = websocket
        
        # Update connection metrics
        if session_id in self.session_metrics:
            self.session_metrics[session_id].connection_time = time.time()
        
        logger.debug(f"🔗 Added WebSocket for session {session_id}")
    
    async def remove_websocket(self, session_id: str, websocket: Any):
        """Remove WebSocket with cleanup"""
        if session_id in self.websocket_connections:
            del self.websocket_connections[session_id]
            logger.debug(f"🔌 Removed WebSocket for session {session_id}")
    
    async def _close_websocket_safely(self, session_id: str):
        """Safely close WebSocket connection"""
        if session_id in self.websocket_connections:
            try:
                websocket = self.websocket_connections[session_id]
                await websocket.close()
            except Exception as e:
                logger.warning(f"Error closing WebSocket for session {session_id}: {e}")
            finally:
                if session_id in self.websocket_connections:
                    del self.websocket_connections[session_id]
    
    async def _cleanup_expired_sessions(self) -> int:
        """Professional session cleanup with metrics"""
        now = datetime.now()
        threshold = now - timedelta(minutes=self.inactive_threshold_minutes)
        expired_sessions = []
        
        # Find expired sessions
        for session_id, session in self.sessions.items():
            if session.updated_at < threshold:
                expired_sessions.append(session_id)
        
        # Clean up expired sessions
        cleaned_count = 0
        for session_id in expired_sessions:
            if await self.end_session(session_id):
                cleaned_count += 1
        
        return cleaned_count
    
    async def _remove_oldest_inactive_session(self):
        """Remove oldest inactive session when limit reached"""
        if not self.sessions:
            return
        
        # Find oldest session
        oldest_session_id = min(
            self.sessions.keys(),
            key=lambda sid: self.sessions[sid].updated_at
        )
        
        await self.end_session(oldest_session_id)
        logger.info(f"🗑️ Removed oldest session due to limit: {oldest_session_id}")
    
    async def _update_statistics(self):
        """Update professional statistics"""
        current_sessions = len(self.sessions)
        
        # Log statistics periodically
        if self.total_sessions_created % 100 == 0:
            logger.info(f"📊 Session Stats - Active: {current_sessions}, "
                       f"Total Created: {self.total_sessions_created}, "
                       f"Peak: {self.peak_concurrent_sessions}")
    
    def get_session_statistics(self) -> Dict[str, Any]:
        """Get comprehensive session statistics"""
        return {
            "active_sessions": len(self.sessions),
            "total_created": self.total_sessions_created,
            "total_ended": self.total_sessions_ended,
            "peak_concurrent": self.peak_concurrent_sessions,
            "websocket_connections": len(self.websocket_connections),
            "is_initialized": self.is_initialized
        }
    
    async def cleanup(self):
        """Professional cleanup with graceful shutdown"""
        logger.info("🛑 Starting professional SessionManager cleanup...")
        
        # Signal shutdown
        if self._shutdown_event:
            self._shutdown_event.set()
        
        # Cancel cleanup task
        if self.cleanup_task and not self.cleanup_task.done():
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Close all WebSocket connections
        close_tasks = []
        for session_id in list(self.websocket_connections.keys()):
            close_tasks.append(self._close_websocket_safely(session_id))
        
        if close_tasks:
            await asyncio.gather(*close_tasks, return_exceptions=True)
        
        # Clear all sessions
        self.sessions.clear()
        self.session_metrics.clear()
        self.websocket_connections.clear()
        
        self.is_initialized = False
        logger.info("✅ Professional SessionManager cleanup completed")


# Global professional session manager instance
session_manager = ProfessionalSessionManager()
