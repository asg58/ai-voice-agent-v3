from memory.memory_manager import MemoryManager

class KnowledgeGraphs:
    def __init__(self, memory_manager: MemoryManager = None):
        self.memory_manager = memory_manager

    def build_graph(self, data):
        """
        Bouw een kennisgrafiek en sla op via MemoryManager (object of vector).
        """
        if self.memory_manager:
            return self.memory_manager.save("knowledge:graph", data, type_="object")
        # Fallback mock
        return f"Knowledge graph built with data: {data}"
