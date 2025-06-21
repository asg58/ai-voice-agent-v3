import redis
import psycopg2
from memory.memory_manager import MemoryManager


class ConsciousAIMemory:
    def __init__(self, memory_manager: MemoryManager = None, redis_client=None, db_connection=None):
        self.memory_manager = memory_manager
        self.redis_client = redis_client or redis.StrictRedis(host='localhost', port=6379, db=0)
        self.db_connection = db_connection or psycopg2.connect(
            dbname="voiceai_db", user="voiceai_user", password="securepassword", host="localhost", port=5432
        )

    def reflect_on_actions(self, actions):
        """
        Simuleer bewustzijn en zelfreflectie via MemoryManager (object).
        Integreer met Redis en PostgreSQL voor opslag.
        """
        if self.memory_manager:
            self.memory_manager.save("conscious:actions", actions, type_="object")
        
        # Opslaan in Redis
        self.redis_client.set("conscious:actions", str(actions))

        # Opslaan in PostgreSQL
        with self.db_connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO actions_reflection (actions) VALUES (%s)",
                (str(actions),)
            )
            self.db_connection.commit()

        return f"Reflected on actions and saved to Redis and PostgreSQL: {actions}"
