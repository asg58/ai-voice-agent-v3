"""
Voorbeeld: Integratie van echte Redis, MinIO, Database en Weaviate clients met de MemoryManager
"""
import redis
from minio import Minio
# from sqlalchemy.orm import Session
# from weaviate import Client as WeaviateClient
from memory.backends import RedisBackend, MinioBackend, DatabaseBackend, VectorDBBackend
from memory.memory_manager import MemoryManager

# Redis client
redis_client = redis.Redis(host='localhost', port=6379, db=0)
redis_backend = RedisBackend(client=redis_client)

# MinIO client
minio_client = Minio(
    'localhost:9000',
    access_key='minioadmin',
    secret_key='minioadmin',
    secure=False
)
minio_backend = MinioBackend(client=minio_client)

# Database backend (voorbeeld, afhankelijk van ORM)
db_backend = DatabaseBackend(session=None)  # Vervang door echte SQLAlchemy session

# VectorDB backend (voorbeeld)
# vector_client = WeaviateClient("http://localhost:8080")
vector_backend = VectorDBBackend(client=None)  # Vervang door echte client

# MemoryManager initialiseren
memory_manager = MemoryManager(
    redis=redis_backend,
    db=db_backend,
    minio=minio_backend,
    vector_db=vector_backend
)

# Gebruik
memory_manager.save("session:123", "Hallo wereld!", type_="short_term")
value = memory_manager.get("session:123", type_="short_term")
print("Redis value:", value)

# Voor MinIO, DB, VectorDB: zie backends.py voor methodesignatures
