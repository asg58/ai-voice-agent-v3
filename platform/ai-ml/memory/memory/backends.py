"""
Backends: Abstracties/wrappers voor Redis, MinIO, Database, Weaviate
"""

class RedisBackend:
    def __init__(self, client):
        self.client = client
    def set(self, key, value):
        return self.client.set(key, value)
    def get(self, key):
        return self.client.get(key)

class MinioBackend:
    def __init__(self, client):
        self.client = client
    def put_object(self, key, value):
        # Vereenvoudigd voorbeeld
        return self.client.put_object("bucket", key, value, len(value))
    def get_object(self, key):
        return self.client.get_object("bucket", key)

class DatabaseBackend:
    def __init__(self, session):
        self.session = session
    def save(self, key, value):
        # Vereenvoudigd voorbeeld
        # self.session.add(...)
        return True
    def get(self, key):
        # self.session.query(...)
        return None

class VectorDBBackend:
    def __init__(self, client):
        self.client = client
    def add_vector(self, key, value):
        return self.client.add(key, value)
    def get_vector(self, key):
        return self.client.get(key)
