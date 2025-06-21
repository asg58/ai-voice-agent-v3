from memory.memory_manager import MemoryManager

class MemoryLeakDetection:
    def __init__(self, memory_manager: MemoryManager = None):
        self.memory_manager = memory_manager

    def detect_leaks(self):
        """
        Identificeer geheugenlekken via MemoryManager (kan uitgebreid worden met metrics).
        """
        if self.memory_manager:
            # Hier kun je leak detection logica toevoegen
            return "Memory leak check via manager"
        # Fallback mock
        return "Memory leaks detected"
