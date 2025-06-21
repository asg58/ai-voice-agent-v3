from memory.memory_manager import MemoryManager

class ShortTermMemoryOptimization:
    def __init__(self, memory_manager: MemoryManager = None):
        self.memory_manager = memory_manager

    def manage_memory(self, temporary_data):
        """
        Beheer tijdelijke context efficiënt via MemoryManager (short_term).
        """
        if self.memory_manager:
            return self.memory_manager.save("shortterm:data", temporary_data, type_="short_term")
        # Fallback mock
        return f"Temporary data managed: {temporary_data}"
