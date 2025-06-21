"""
Database Models for Memory System
"""
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Text, Integer, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field

Base = declarative_base()

# SQLAlchemy Models
class Conversation(Base):
    """Database model for conversation"""
    __tablename__ = "conversations"
    
    session_id = Column(String(36), primary_key=True)
    user_id = Column(String(36), nullable=False)
    created_at = Column(DateTime, nullable=False)
    last_activity = Column(DateTime, nullable=False)
    language = Column(String(10), nullable=True)
    conversation_metadata = Column(JSON, nullable=True)
    
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Conversation(session_id={self.session_id}, user_id={self.user_id})>"


class Message(Base):
    """Database model for message"""
    __tablename__ = "messages"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String(36), ForeignKey("conversations.session_id"), nullable=False)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    vector_id = Column(String(36), nullable=True)  # Reference to vector in Weaviate
    message_metadata = Column(JSON, nullable=True)
    
    conversation = relationship("Conversation", back_populates="messages")
    
    def __repr__(self):
        return f"<Message(id={self.id}, role={self.role})>"


class Entity(Base):
    """Database model for entity"""
    __tablename__ = "entities"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    entity_type = Column(String(50), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    last_updated = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    entity_metadata = Column(JSON, nullable=True)
    
    def __repr__(self):
        return f"<Entity(id={self.id}, name={self.name}, type={self.entity_type})>"


class EntityRelation(Base):
    """Database model for entity relation"""
    __tablename__ = "entity_relations"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_id = Column(String(36), ForeignKey("entities.id"), nullable=False)
    target_id = Column(String(36), ForeignKey("entities.id"), nullable=False)
    relation_type = Column(String(50), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    confidence = Column(Float, nullable=True)
    relation_metadata = Column(JSON, nullable=True)
    
    def __repr__(self):
        return f"<EntityRelation(source={self.source_id}, relation={self.relation_type}, target={self.target_id})>"


# Pydantic Models for API
class MessageData(BaseModel):
    """Message data model"""
    id: Optional[str] = None
    role: str
    content: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        orm_mode = True


class ConversationData(BaseModel):
    """Conversation data model"""
    session_id: str
    user_id: str
    created_at: datetime
    last_activity: datetime
    language: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    messages: Optional[List[MessageData]] = None
    
    class Config:
        orm_mode = True


class EntityData(BaseModel):
    """Entity data model"""
    id: Optional[str] = None
    name: str
    entity_type: str
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        orm_mode = True


class RelationData(BaseModel):
    """Relation data model"""
    source: EntityData
    relation_type: str
    target: EntityData
    confidence: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        orm_mode = True


class MemorySearchResult(BaseModel):
    """Memory search result model"""
    messages: List[MessageData] = Field(default_factory=list)
    entities: List[EntityData] = Field(default_factory=list)
    relations: List[RelationData] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = None