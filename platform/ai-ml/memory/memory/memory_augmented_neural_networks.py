from memory.memory_manager import MemoryManager


class MemoryAugmentedNeuralNetworks:
    def __init__(self, memory_manager: MemoryManager = None):
        self.memory_manager = memory_manager

    def enhance_memory(self, model, memory_data):
        """
        Verbeter het geheugen van AI-modellen via MemoryManager (vector).
        """
        if self.memory_manager:
            return self.memory_manager.save(f"model:{model}:memory", memory_data, type_="vector")
        # Fallback mock
        return f"Model memory enhanced with data: {memory_data}"
