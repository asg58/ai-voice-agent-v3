from memory.memory_manager import MemoryManager

class AttentionMechanisms:
    def __init__(self, memory_manager: MemoryManager = None):
        self.memory_manager = memory_manager

    def optimize_attention(self, model, input_data):
        """
        Optimaliseer aandachtmechanismen via MemoryManager (vector).
        """
        if self.memory_manager:
            return self.memory_manager.save(f"attention:{model}", input_data, type_="vector")
        # Fallback mock
        return f"Attention optimized for input: {input_data}"
