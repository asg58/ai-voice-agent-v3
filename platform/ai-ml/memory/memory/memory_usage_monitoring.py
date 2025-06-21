from memory.memory_manager import MemoryManager

class MemoryUsageMonitoring:
    def __init__(self, memory_manager: MemoryManager = None):
        self.memory_manager = memory_manager

    def monitor_usage(self):
        """
        Analyseer geheugengebruik via MemoryManager (kan uitgebreid worden met metrics).
        """
        if self.memory_manager:
            # Hier kun je metrics ophalen uit de backends
            return {
                "redis": str(self.memory_manager.redis),
                "db": str(self.memory_manager.db),
                "minio": str(self.memory_manager.minio),
                "vector_db": str(self.memory_manager.vector_db)
            }
        # Fallback mock
        return "Memory usage monitored"
