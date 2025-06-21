"""
MemoryManager: Centrale orchestrator voor alle memory backends (Redis, MinIO, DB, VectorDB)
"""
from typing import Optional

class MemoryManager:
    """
    Centrale orchestrator die automatisch de juiste backend kiest voor memory operations.
    - Short-term/session: Redis
    - Long-term/knowledge: Database
    - Object: MinIO
    - Vector: Weaviate
    """
    def __init__(self, redis=None, db=None, minio=None, vector_db=None):
        self.redis = redis
        self.db = db
        self.minio = minio
        self.vector_db = vector_db

    def save(self, key: str, value, type_: str = "short_term"):
        if type_ == "short_term" and self.redis:
            return self.redis.set(key, value)
        elif type_ == "long_term" and self.db:
            # Vereenvoudigd voorbeeld
            return self.db.save(key, value)
        elif type_ == "object" and self.minio:
            return self.minio.put_object(key, value)
        elif type_ == "vector" and self.vector_db:
            return self.vector_db.add_vector(key, value)
        else:
            raise ValueError("No backend available for type: " + type_)

    def get(self, key: str, type_: str = "short_term"):
        if type_ == "short_term" and self.redis:
            return self.redis.get(key)
        elif type_ == "long_term" and self.db:
            return self.db.get(key)
        elif type_ == "object" and self.minio:
            return self.minio.get_object(key)
        elif type_ == "vector" and self.vector_db:
            return self.vector_db.get_vector(key)
        else:
            raise ValueError("No backend available for type: " + type_)

    # Uitbreidbaar met monitoring, fallback, security, etc.
