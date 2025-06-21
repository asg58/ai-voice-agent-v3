from memory.memory_manager import MemoryManager

class InfiniteContextAwareness:
    def __init__(self, memory_manager: MemoryManager = None):
        self.memory_manager = memory_manager

    def combine_contexts(self, contexts):
        """
        Combineer alle contexten dynamisch via MemoryManager (object).
        """
        if self.memory_manager:
            return self.memory_manager.save("infinite:contexts", contexts, type_="object")
        # Fallback mock
        return f"Combined contexts: {contexts}"
