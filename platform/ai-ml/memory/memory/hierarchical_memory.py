from memory.memory_manager import MemoryManager

class HierarchicalMemory:
    def __init__(self, memory_manager: MemoryManager = None):
        self.memory_manager = memory_manager

    def organize_memory(self, data):
        """
        Organiseer informatie in een hiërarchisch geheugen via MemoryManager (object).
        """
        if self.memory_manager:
            return self.memory_manager.save("hierarchical:memory", data, type_="object")
        # Fallback mock
        return f"Hierarchical memory organized with data: {data}"
