"""
Productie-integratie: MemoryManager met echte Redis, MinIO, PostgreSQL en Weaviate backends
"""
import redis
from minio import Minio
import psycopg2
# from weaviate import Client as WeaviateClient
from memory.backends import RedisBackend, MinioBackend, DatabaseBackend, VectorDBBackend
from memory.memory_manager import MemoryManager

# Redis client
redis_client = redis.Redis(host='redis', port=6379, db=0)
redis_backend = RedisBackend(client=redis_client)

# MinIO client
minio_client = Minio(
    'minio:9000',
    access_key='minioadmin',
    secret_key='minioadmin',
    secure=False
)
minio_backend = MinioBackend(client=minio_client)

# PostgreSQL client (vereenvoudigd)
pg_conn = psycopg2.connect(
    host='postgres',
    port=5432,
    user='voiceai_user',
    password='secure_password_change_me',
    dbname='voiceai_db'
)
db_backend = DatabaseBackend(session=pg_conn)

# VectorDB backend (voorbeeld, uit te breiden)
# vector_client = WeaviateClient("http://weaviate:8080")
vector_backend = VectorDBBackend(client=None)

# MemoryManager initialiseren
memory_manager = MemoryManager(
    redis=redis_backend,
    db=db_backend,
    minio=minio_backend,
    vector_db=vector_backend
)

# Voorbeeldgebruik
memory_manager.save("session:prod", "Productie test", type_="short_term")
value = memory_manager.get("session:prod", type_="short_term")
print("Redis value:", value)
