from memory.memory_manager import MemoryManager
from memory.backends import RedisBackend
import redis

# Productie-integratie: koppel dashboard direct aan Redis via MemoryManager
redis_client = redis.Redis(host='redis', port=6379, db=0)
redis_backend = RedisBackend(client=redis_client)
memory_manager = MemoryManager(redis=redis_backend)

# Voorbeeld: dashboard haalt statistieken uit Redis via MemoryManager

def get_dashboard_stat(key):
    value = memory_manager.get(key, type_="short_term")
    return value

class Dashboard:
    def display_kpis(self, kpi_data):
        """
        Toon zakelijke inzichten en KPI's.
        """
        # Mock implementatie
        return {"dashboard": kpi_data}
