from memory.memory_manager import MemoryManager


class SelfEvolvingMemory:
    def __init__(self, memory_manager: MemoryManager = None):
        self.memory_manager = memory_manager

    def evolve_memory(self, usage_patterns):
        """
        Optimaliseer en breid geheugen uit via MemoryManager (object).
        """
        if self.memory_manager:
            return self.memory_manager.save("selfevolving:patterns", usage_patterns, type_="object")
        # Fallback mock
        return f"Memory evolved with patterns: {usage_patterns}"
