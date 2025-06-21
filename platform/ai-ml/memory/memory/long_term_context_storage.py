from memory.memory_manager import MemoryManager

class LongTermContextStorage:
    def __init__(self, memory_manager: MemoryManager = None):
        self.memory_manager = memory_manager

    def store_context(self, context):
        """
        Sla langdurige context op via MemoryManager (long_term).
        """
        if self.memory_manager:
            return self.memory_manager.save("longterm:context", context, type_="long_term")
        # Fallback mock
        return f"Context stored: {context}"

    def retrieve_context(self):
        """
        Haal langdurige context op via MemoryManager (long_term).
        """
        if self.memory_manager:
            return self.memory_manager.get("longterm:context", type_="long_term")
        # Fallback mock
        return "Retrieved long-term context"
