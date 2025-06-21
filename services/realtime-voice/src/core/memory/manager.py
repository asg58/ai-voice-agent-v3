"""
Memory Manager for AI Voice Agent
Handles short-term and long-term memory, knowledge graphs, and vector search
"""
import logging
import asyncio
import json
import time
import uuid
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timedelta

import redis.asyncio as redis
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import weaviate
from weaviate.util import generate_uuid5
import weaviate.classes as wvc

from src.config import settings
from src.models import MemoryCapabilities, ConversationSession
from src.core.conversation.models import ConversationMessage
from src.core.memory.models import (
    Conversation, Message, Entity, EntityRelation,
    ConversationData, MessageData, EntityData, RelationData, MemorySearchResult
)
from src.core.memory.database import database

# Initialize logger first
logger = logging.getLogger(__name__)

# Import neo4j with fallback handling
try:
    import neo4j
    NEO4J_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Neo4j not available: {e}. Knowledge graph features will be disabled.")
    neo4j = None
    NEO4J_AVAILABLE = False

class MemoryCache:
    """Simple memory cache with TTL support"""
    
    def __init__(self, max_size: int = 1000):
        """Initialize memory cache"""
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.max_size = max_size
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if key not in self.cache:
            return None
            
        item = self.cache[key]
        
        # Check if expired
        if item["expires_at"] and item["expires_at"] < time.time():
            del self.cache[key]
            return None
            
        # Update last access time
        item["last_access"] = time.time()
        return item["value"]
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in cache with optional TTL"""
        # Check if cache is full
        if len(self.cache) >= self.max_size and key not in self.cache:
            # Remove oldest item (simple LRU)
            oldest_key = min(self.cache.items(), key=lambda x: x[1]["last_access"])[0]
            del self.cache[oldest_key]
        
        # Set item
        self.cache[key] = {
            "value": value,
            "last_access": time.time(),
            "expires_at": time.time() + ttl if ttl else None
        }
    
    def delete(self, key: str) -> bool:
        """Delete item from cache"""
        if key in self.cache:
            del self.cache[key]
            return True
        return False
    
    def clear(self):
        """Clear cache"""
        self.cache.clear()


class MemoryManager:
    """Memory manager for AI Voice Agent"""
    
    def __init__(self):
        """Initialize memory manager"""
        self.initialized = False
        self.redis_client = None
        self.vector_db = None
        self.graph_db = None
        self.cache = MemoryCache(max_size=1000)
    
    async def initialize(self):
        """Initialize memory backends"""
        logger.info("Initializing memory manager")
        
        try:
            # Initialize database
            db_initialized = await database.initialize()
            if db_initialized:
                await database.create_tables()
            
            # Initialize Redis if enabled
            if settings.MEMORY_ENABLED:
                await self._initialize_redis()
            
            # Initialize vector database if enabled
            if settings.VECTOR_SEARCH_ENABLED:
                await self._initialize_vector_db()
            
            # Initialize knowledge graph if enabled
            if settings.KNOWLEDGE_GRAPH_ENABLED:
                await self._initialize_knowledge_graph()
            
            self.initialized = True
            logger.info("Memory manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize memory manager: {str(e)}")
            raise
    
    async def _initialize_redis(self):
        """Initialize Redis client"""
        try:
            # Check if REDIS_URL is provided (for Docker deployment)
            import os
            redis_url = os.getenv("REDIS_URL")
            if redis_url:
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
            else:
                self.redis_client = redis.Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    db=settings.REDIS_DB,
                    password=settings.REDIS_PASSWORD,
                    decode_responses=True
                )
            
            # Test connection
            await self.redis_client.ping()
            logger.info("Redis connection successful")
            
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {str(e)}")
            self.redis_client = None
    
    async def _initialize_vector_db(self):
        """Initialize vector database"""
        try:            # Check if WEAVIATE_URL is provided (for Docker deployment)
            import os
            weaviate_url = os.getenv("WEAVIATE_URL")
            if weaviate_url:
                self.vector_db = weaviate.connect_to_custom(weaviate_url)
            else:
                # Initialize Weaviate client with individual settings
                self.vector_db = weaviate.connect_to_custom(
                    http_host=settings.WEAVIATE_HOST,
                    http_port=settings.WEAVIATE_PORT,
                    http_secure=settings.WEAVIATE_SCHEME == "https"
                )
            
            # Check if schema exists and create if needed
            try:
                # Try to get the Message collection
                message_collection = self.vector_db.collections.get("Message")
            except Exception:
                # Collection doesn't exist, create schema
                self._create_vector_schema()                
            logger.info("Vector database initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize vector database: {str(e)}")
            self.vector_db = None

    def _create_vector_schema(self):
        """Create schema for vector database"""
        # Import required classes for v4 API
        import weaviate.classes as wvc
        
        # Create Message collection with v4 API
        message_collection = self.vector_db.collections.create(
            name="Message",
            description="A message in a conversation",
            properties=[
                wvc.config.Property(name="content", data_type=wvc.config.DataType.TEXT, description="Message content"),
                wvc.config.Property(name="role", data_type=wvc.config.DataType.TEXT, description="Message role (user, assistant, system)"),
                wvc.config.Property(name="conversationId", data_type=wvc.config.DataType.TEXT, description="ID of the conversation"),
                wvc.config.Property(name="timestamp", data_type=wvc.config.DataType.DATE, description="Message timestamp"),
                wvc.config.Property(name="language", data_type=wvc.config.DataType.TEXT, description="Message language")
            ],
            vectorizer_config=wvc.config.Configure.Vectorizer.none(),  # Use custom vectors
            vector_index_config=wvc.config.Configure.VectorIndex.hnsw(distance_metric=wvc.config.VectorDistances.COSINE)
        )
        
        logger.info("Created vector schema for Message class")
    
    async def _initialize_knowledge_graph(self):
        """Initialize knowledge graph"""
        if not NEO4J_AVAILABLE:
            logger.warning("Neo4j driver not available - knowledge graph initialization skipped")
            self.graph_db = None
            return
            
        try:
            # Initialize Neo4j client
            self.graph_db = neo4j.AsyncGraphDatabase.driver(
                f"neo4j://{settings.NEO4J_HOST}:{settings.NEO4J_PORT}",
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
            )
            
            # Test connection
            async with self.graph_db.session() as session:
                result = await session.run("RETURN 1 as test")
                record = await result.single()
                if record and record["test"] == 1:
                    logger.info("Knowledge graph connection successful")
                
        except Exception as e:
            logger.error(f"Failed to initialize knowledge graph: {str(e)}")
            self.graph_db = None
    
    async def health_check(self) -> Dict[str, str]:
        """Check health of memory backends"""
        if not self.initialized:
            return {
                "status": "not_initialized",
                "redis": "not_connected",
                "database": "not_connected",
                "vector_db": "not_connected",
                "graph_db": "not_connected"
            }
        
        status = {
            "status": "ok",
            "database": "ok" if database.initialized else "not_connected",
            "redis": "ok" if self.redis_client else "not_connected",
            "vector_db": "ok" if self.vector_db else "not_connected",
            "graph_db": "ok" if self.graph_db else "not_connected"
        }
        
        # Check Redis connection
        if self.redis_client:
            try:
                await self.redis_client.ping()
            except Exception:
                status["redis"] = "error"
                status["status"] = "degraded"
        
        return status
    
    async def get_capabilities(self) -> MemoryCapabilities:
        """Get memory system capabilities"""
        return MemoryCapabilities(
            short_term=self.redis_client is not None,
            long_term=database.initialized,
            knowledge_graph=self.graph_db is not None,
            vector_search=self.vector_db is not None
        )
    
    # Session management methods
    
    async def store_session(self, session_id: str, data: Dict[str, Any], expire_seconds: int = None) -> bool:
        """Store session data in Redis"""
        if not self.redis_client:
            return False
            
        try:
            # Use default TTL if not specified
            if expire_seconds is None:
                expire_seconds = settings.SHORT_TERM_MEMORY_TTL
                
            # Store in Redis
            key = f"session:{session_id}"
            serialized = json.dumps(data)
            await self.redis_client.set(key, serialized, ex=expire_seconds)
            
            # Also store in local cache
            self.cache.set(key, data, ttl=expire_seconds)
            
            return True
            
        except Exception as e:
            logger.error(f"Error storing session {session_id}: {str(e)}")
            return False
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data from Redis"""
        # Try local cache first
        key = f"session:{session_id}"
        cached_data = self.cache.get(key)
        if cached_data:
            return cached_data
            
        # Try Redis
        if not self.redis_client:
            return None
            
        try:
            data = await self.redis_client.get(key)
            if data:
                parsed_data = json.loads(data)
                # Update cache
                self.cache.set(key, parsed_data)
                return parsed_data
                
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving session {session_id}: {str(e)}")
            return None
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete session data from Redis"""
        # Delete from cache
        key = f"session:{session_id}"
        self.cache.delete(key)
        
        # Delete from Redis
        if not self.redis_client:
            return False
            
        try:
            await self.redis_client.delete(key)
            return True
            
        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {str(e)}")
            return False
    
    # Conversation storage methods
    
    async def store_conversation(self, conversation: ConversationSession) -> bool:
        """Store conversation in database"""
        if not database.initialized:
            return False
            
        try:
            async for session in database.get_session():
                # Check if conversation exists
                stmt = select(Conversation).where(Conversation.session_id == conversation.session_id)
                result = await session.execute(stmt)
                db_conversation = result.scalars().first()
                
                if db_conversation:
                    # Update existing conversation
                    db_conversation.last_activity = conversation.last_activity
                    db_conversation.metadata = conversation.metadata
                else:
                    # Create new conversation
                    db_conversation = Conversation(
                        session_id=conversation.session_id,
                        user_id=conversation.user_id,
                        created_at=conversation.created_at,
                        last_activity=conversation.last_activity,
                        metadata=conversation.metadata
                    )
                    session.add(db_conversation)
                
                # Commit changes
                await session.commit()
                
                return True
                
        except Exception as e:
            logger.error(f"Error storing conversation {conversation.session_id}: {str(e)}")
            return False
    
    async def store_message(self, session_id: str, message: ConversationMessage) -> Optional[str]:
        """Store message in database and vector database"""
        if not database.initialized:
            return None
            
        try:
            # Generate message ID if not provided
            message_id = str(uuid.uuid4())
            vector_id = None
            
            # Store in vector database if enabled
            if self.vector_db and settings.VECTOR_SEARCH_ENABLED:
                vector_id = await self._store_message_vector(session_id, message)
            
            # Store in database
            async for session in database.get_session():
                db_message = Message(
                    id=message_id,
                    conversation_id=session_id,
                    role=message.role,
                    content=message.content,
                    timestamp=message.timestamp,
                    vector_id=vector_id,
                    metadata=message.metadata
                )
                
                session.add(db_message)
                await session.commit()
                
                return message_id
                
        except Exception as e:
            logger.error(f"Error storing message for session {session_id}: {str(e)}")
            return None
    
    async def _store_message_vector(self, session_id: str, message: ConversationMessage) -> Optional[str]:
        """Store message in vector database"""
        if not self.vector_db:
            return None
            
        try:
            # Generate deterministic UUID based on session_id and timestamp
            vector_id = generate_uuid5(f"{session_id}:{message.timestamp.isoformat()}:{message.content[:50]}")
            
            # Create data object
            data_object = {
                "content": message.content,
                "role": message.role,
                "conversationId": session_id,
                "timestamp": message.timestamp.isoformat(),
                "language": message.metadata.get("language", "nl") if message.metadata else "nl"
            }
            
            # Store in Weaviate
            self.vector_db.data_object.create(
                data_object=data_object,
                class_name="Message",
                uuid=vector_id
            )
            
            return vector_id
            
        except Exception as e:
            logger.error(f"Error storing message vector: {str(e)}")
            return None
    
    async def get_conversation_history(self, session_id: str, limit: int = 50) -> List[MessageData]:
        """Get conversation history from database"""
        if not database.initialized:
            return []
            
        try:
            async for session in database.get_session():
                # Query messages
                stmt = (
                    select(Message)
                    .where(Message.conversation_id == session_id)
                    .order_by(desc(Message.timestamp))
                    .limit(limit)
                )
                
                result = await session.execute(stmt)
                messages = result.scalars().all()
                
                # Convert to MessageData
                return [
                    MessageData(
                        id=msg.id,
                        role=msg.role,
                        content=msg.content,
                        timestamp=msg.timestamp,
                        metadata=msg.metadata
                    )
                    for msg in messages
                ]
                
        except Exception as e:
            logger.error(f"Error retrieving conversation history for {session_id}: {str(e)}")
            return []
    
    # Semantic search methods
    
    async def semantic_search(self, query: str, limit: int = 5) -> List[MessageData]:
        """Search for semantically similar messages"""
        if not self.vector_db or not settings.VECTOR_SEARCH_ENABLED:
            return []
            
        try:
            # Perform semantic search
            result = (
                self.vector_db.query
                .get("Message", ["content", "role", "conversationId", "timestamp"])
                .with_near_text({"concepts": [query]})
                .with_limit(limit)
                .do()
            )
            
            # Extract messages
            messages = []
            if "data" in result and "Get" in result["data"] and "Message" in result["data"]["Get"]:
                for item in result["data"]["Get"]["Message"]:
                    # Convert to MessageData
                    messages.append(
                        MessageData(
                            role=item["role"],
                            content=item["content"],
                            timestamp=datetime.fromisoformat(item["timestamp"]),
                            metadata={"conversation_id": item["conversationId"]}
                        )
                    )
            
            return messages
            
        except Exception as e:
            logger.error(f"Error performing semantic search: {str(e)}")
            return []
    
    # Knowledge graph methods
    
    async def store_entity(self, name: str, entity_type: str, metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Store entity in database and knowledge graph"""
        if not database.initialized:
            return None
            
        try:
            entity_id = str(uuid.uuid4())
            
            # Store in database
            async for session in database.get_session():
                # Check if entity exists
                stmt = select(Entity).where(
                    Entity.name == name,
                    Entity.entity_type == entity_type
                )
                result = await session.execute(stmt)
                db_entity = result.scalars().first()
                
                if db_entity:
                    # Update existing entity
                    db_entity.last_updated = datetime.now()
                    if metadata:
                        db_entity.metadata = metadata
                    entity_id = db_entity.id
                else:
                    # Create new entity
                    db_entity = Entity(
                        id=entity_id,
                        name=name,
                        entity_type=entity_type,
                        metadata=metadata
                    )
                    session.add(db_entity)
                
                await session.commit()
            
            # Store in knowledge graph if enabled
            if self.graph_db and settings.KNOWLEDGE_GRAPH_ENABLED:
                await self._store_entity_in_graph(entity_id, name, entity_type, metadata)
            
            return entity_id
            
        except Exception as e:
            logger.error(f"Error storing entity {name}: {str(e)}")
            return None
    
    async def _store_entity_in_graph(self, entity_id: str, name: str, entity_type: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Store entity in knowledge graph"""
        if not self.graph_db:
            return False
            
        try:
            async with self.graph_db.session() as session:
                # Create entity
                query = (
                    "MERGE (e:Entity {id: $id}) "
                    "SET e.name = $name, e.type = $type, e.updated = datetime() "
                )
                
                params = {
                    "id": entity_id,
                    "name": name,
                    "type": entity_type
                }
                
                # Add metadata if provided
                if metadata:
                    query += ", e.metadata = $metadata "
                    params["metadata"] = json.dumps(metadata)
                
                # Execute query
                await session.run(query, params)
                
                return True
                
        except Exception as e:
            logger.error(f"Error storing entity in graph: {str(e)}")
            return False
    
    async def store_relation(self, source_id: str, relation_type: str, target_id: str, confidence: float = 1.0, metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Store relation between entities"""
        if not database.initialized:
            return None
            
        try:
            relation_id = str(uuid.uuid4())
            
            # Store in database
            async for session in database.get_session():
                # Check if relation exists
                stmt = select(EntityRelation).where(
                    EntityRelation.source_id == source_id,
                    EntityRelation.relation_type == relation_type,
                    EntityRelation.target_id == target_id
                )
                result = await session.execute(stmt)
                db_relation = result.scalars().first()
                
                if db_relation:
                    # Update existing relation
                    db_relation.confidence = confidence
                    if metadata:
                        db_relation.metadata = metadata
                    relation_id = db_relation.id
                else:
                    # Create new relation
                    db_relation = EntityRelation(
                        id=relation_id,
                        source_id=source_id,
                        relation_type=relation_type,
                        target_id=target_id,
                        confidence=confidence,
                        metadata=metadata
                    )
                    session.add(db_relation)
                
                await session.commit()
            
            # Store in knowledge graph if enabled
            if self.graph_db and settings.KNOWLEDGE_GRAPH_ENABLED:
                await self._store_relation_in_graph(source_id, relation_type, target_id, confidence, metadata)
            
            return relation_id
            
        except Exception as e:
            logger.error(f"Error storing relation: {str(e)}")
            return None
    
    async def _store_relation_in_graph(self, source_id: str, relation_type: str, target_id: str, confidence: float = 1.0, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Store relation in knowledge graph"""
        if not self.graph_db:
            return False
            
        try:
            async with self.graph_db.session() as session:
                # Create relation
                query = (
                    "MATCH (source:Entity {id: $source_id}) "
                    "MATCH (target:Entity {id: $target_id}) "
                    "MERGE (source)-[r:" + relation_type + "]->(target) "
                    "SET r.confidence = $confidence, r.updated = datetime() "
                )
                
                params = {
                    "source_id": source_id,
                    "target_id": target_id,
                    "confidence": confidence
                }
                
                # Add metadata if provided
                if metadata:
                    query += ", r.metadata = $metadata "
                    params["metadata"] = json.dumps(metadata)
                
                # Execute query
                await session.run(query, params)
                
                return True
                
        except Exception as e:
            logger.error(f"Error storing relation in graph: {str(e)}")
            return False
    
    async def search_knowledge_graph(self, entity_name: str, relation_type: Optional[str] = None, max_depth: int = 2) -> List[RelationData]:
        """Search knowledge graph for entity and its relations"""
        if not self.graph_db or not settings.KNOWLEDGE_GRAPH_ENABLED:
            return []
            
        try:
            async with self.graph_db.session() as session:
                # Build query
                if relation_type:
                    # Search for specific relation type
                    query = (
                        "MATCH (source:Entity)-[r:" + relation_type + "]->(target:Entity) "
                        "WHERE source.name CONTAINS $name OR target.name CONTAINS $name "
                        "RETURN source, r, target "
                        "LIMIT 10"
                    )
                else:
                    # Search for any relation
                    query = (
                        f"MATCH path = (source:Entity)-[r*1..{max_depth}]-(target:Entity) "
                        "WHERE source.name CONTAINS $name "
                        "RETURN path "
                        "LIMIT 10"
                    )
                
                # Execute query
                result = await session.run(query, {"name": entity_name})
                
                # Process results
                relations = []
                async for record in result:
                    if "path" in record:
                        # Process path
                        path = record["path"]
                        for segment in path:
                            if hasattr(segment, "start_node") and hasattr(segment, "end_node"):
                                source = segment.start_node
                                target = segment.end_node
                                rel = segment
                                
                                relations.append(
                                    RelationData(
                                        source=EntityData(
                                            id=source["id"],
                                            name=source["name"],
                                            entity_type=source["type"]
                                        ),
                                        relation_type=rel.type,
                                        target=EntityData(
                                            id=target["id"],
                                            name=target["name"],
                                            entity_type=target["type"]
                                        ),
                                        confidence=rel.get("confidence", 1.0)
                                    )
                                )
                    else:
                        # Process direct relation
                        source = record["source"]
                        target = record["target"]
                        rel = record["r"]
                        
                        relations.append(
                            RelationData(
                                source=EntityData(
                                    id=source["id"],
                                    name=source["name"],
                                    entity_type=source["type"]
                                ),
                                relation_type=rel.type,
                                target=EntityData(
                                    id=target["id"],
                                    name=target["name"],
                                    entity_type=target["type"]
                                ),
                                confidence=rel.get("confidence", 1.0)
                            )
                        )
                
                return relations
                
        except Exception as e:
            logger.error(f"Error searching knowledge graph: {str(e)}")
            return []
    
    # Memory search methods
    
    async def search_memory(self, query: str, session_id: Optional[str] = None) -> MemorySearchResult:
        """Search memory for relevant information"""
        result = MemorySearchResult()
        
        # Search vector database for similar messages
        if self.vector_db and settings.VECTOR_SEARCH_ENABLED:
            result.messages = await self.semantic_search(query, limit=5)
        
        # Search knowledge graph for relevant entities and relations
        if self.graph_db and settings.KNOWLEDGE_GRAPH_ENABLED:
            # Extract potential entities from query
            # This is a simple implementation - in a real system, use NER
            words = query.split()
            for word in words:
                if len(word) > 3:  # Only consider words with more than 3 characters
                    relations = await self.search_knowledge_graph(word)
                    if relations:
                        result.relations.extend(relations)
                        
                        # Extract entities from relations
                        for relation in relations:
                            if relation.source not in result.entities:
                                result.entities.append(relation.source)
                            if relation.target not in result.entities:
                                result.entities.append(relation.target)
        
        # Get session-specific context if session_id provided
        if session_id:
            session_data = await self.get_session(session_id)
            if session_data:
                result.metadata = {"session_data": session_data}
        
        return result
    
    # Memory management methods
    
    async def cleanup_old_sessions(self, max_age_days: int = 30) -> int:
        """Clean up old sessions from database"""
        if not database.initialized:
            return 0
            
        try:
            cutoff_date = datetime.now() - timedelta(days=max_age_days)
            
            async for session in database.get_session():
                # Find old conversations
                stmt = select(Conversation).where(Conversation.last_activity < cutoff_date)
                result = await session.execute(stmt)
                old_conversations = result.scalars().all()
                
                # Delete old conversations
                for conversation in old_conversations:
                    await session.delete(conversation)
                
                # Commit changes
                await session.commit()
                
                return len(old_conversations)
                
        except Exception as e:
            logger.error(f"Error cleaning up old sessions: {str(e)}")
            return 0
    
    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory usage statistics"""
        stats = {
            "short_term": {
                "enabled": self.redis_client is not None,
                "count": 0
            },
            "long_term": {
                "enabled": database.initialized,
                "conversations": 0,
                "messages": 0
            },
            "vector_search": {
                "enabled": self.vector_db is not None,
                "count": 0
            },
            "knowledge_graph": {
                "enabled": self.graph_db is not None,
                "entities": 0,
                "relations": 0
            }
        }
        
        # Get Redis stats
        if self.redis_client:
            try:
                # Count session keys
                session_count = await self.redis_client.keys("session:*")
                stats["short_term"]["count"] = len(session_count)
            except Exception as e:
                logger.error(f"Error getting Redis stats: {str(e)}")
        
        # Get database stats
        if database.initialized:
            try:
                async for session in database.get_session():
                    # Count conversations
                    conv_count = await session.execute(select(func.count()).select_from(Conversation))
                    stats["long_term"]["conversations"] = conv_count.scalar()
                    
                    # Count messages
                    msg_count = await session.execute(select(func.count()).select_from(Message))
                    stats["long_term"]["messages"] = msg_count.scalar()
                    
                    # Count entities
                    entity_count = await session.execute(select(func.count()).select_from(Entity))
                    stats["knowledge_graph"]["entities"] = entity_count.scalar()
                    
                    # Count relations
                    relation_count = await session.execute(select(func.count()).select_from(EntityRelation))
                    stats["knowledge_graph"]["relations"] = relation_count.scalar()
            except Exception as e:
                logger.error(f"Error getting database stats: {str(e)}")
        
        # Get vector database stats
        if self.vector_db:
            try:
                result = self.vector_db.query.aggregate("Message").with_meta_count().do()
                if "data" in result and "Aggregate" in result["data"] and "Message" in result["data"]["Aggregate"]:
                    stats["vector_search"]["count"] = result["data"]["Aggregate"]["Message"]["meta"]["count"]
            except Exception as e:
                logger.error(f"Error getting vector database stats: {str(e)}")
        
        return stats
    
    async def close(self):
        """Close memory backends"""
        logger.info("Closing memory manager")
        
        # Close Redis connection
        if self.redis_client:
            await self.redis_client.close()
            self.redis_client = None
        
        # Close database connection
        await database.close()
        
        # Close Neo4j connection
        if self.graph_db:
            await self.graph_db.close()
            self.graph_db = None
        
        # Clear cache
        self.cache.clear()
        
        self.initialized = False
        logger.info("Memory manager closed")


# Create singleton instance
memory_manager = MemoryManager()