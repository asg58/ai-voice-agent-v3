"""
Simple Session Manager for Phase 2
Working implementation without complex dependencies
"""
import asyncio
import logging
from typing import Dict, Optional
from datetime import datetime, timedelta
import uuid

from .models import ConversationSession

logger = logging.getLogger(__name__)

class SimpleSessionManager:
    """Simplified Session Manager that works reliably"""
    
    def __init__(self):
        self.sessions: Dict[str, ConversationSession] = {}
        self.websocket_connections: Dict[str, any] = {}
        self.max_sessions = 1000
        logger.info("SimpleSessionManager initialized")
    
    async def initialize(self):
        """Initialize the session manager"""
        logger.info("Session manager initialized")
    
    async def create_session(self, user_id: Optional[str] = None) -> ConversationSession:
        """Create a new conversation session"""
        session_id = str(uuid.uuid4())
        session = ConversationSession(
            session_id=session_id,
            user_id=user_id,
            status="active",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            messages=[],
            metadata={}
        )
        
        # Check session limit
        if len(self.sessions) >= self.max_sessions:
            # Remove oldest session
            oldest_id = min(self.sessions.keys(), 
                          key=lambda x: self.sessions[x].created_at)
            await self.end_session(oldest_id)
        
        self.sessions[session_id] = session
        logger.info(f"Created session: {session_id}")
        return session
    
    async def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """Get session by ID"""
        session = self.sessions.get(session_id)
        if session:
            session.updated_at = datetime.now()
        return session
    
    async def end_session(self, session_id: str) -> bool:
        """End a session"""
        if session_id in self.sessions:
            # Close websocket if exists
            if session_id in self.websocket_connections:
                try:
                    websocket = self.websocket_connections[session_id]
                    await websocket.close()
                except:
                    pass
                del self.websocket_connections[session_id]
            
            del self.sessions[session_id]
            logger.info(f"Ended session: {session_id}")
            return True
        return False
    
    async def add_websocket(self, session_id: str, websocket):
        """Add websocket to session"""
        self.websocket_connections[session_id] = websocket
        logger.debug(f"Added WebSocket for session {session_id}")
    
    async def remove_websocket(self, session_id: str, websocket):
        """Remove websocket from session"""
        if session_id in self.websocket_connections:
            del self.websocket_connections[session_id]
            logger.debug(f"Removed WebSocket for session {session_id}")
    
    async def cleanup(self):
        """Cleanup all sessions"""
        for session_id in list(self.sessions.keys()):
            await self.end_session(session_id)
        logger.info("All sessions cleaned up")

# Global session manager instance
simple_session_manager = SimpleSessionManager()
