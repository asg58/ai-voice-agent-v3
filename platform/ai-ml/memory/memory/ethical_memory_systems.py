from memory.memory_manager import MemoryManager


class EthicalMemorySystems:
    def __init__(self, memory_manager: MemoryManager = None):
        self.memory_manager = memory_manager

    def make_decision(self, ethical_dilemma):
        """
        Neem ethische beslissingen en respecteer waarden via MemoryManager (object).
        """
        if self.memory_manager:
            return self.memory_manager.save("ethical:dilemma", ethical_dilemma, type_="object")
        # Fallback mock
        return f"Decision made for dilemma: {ethical_dilemma}"
