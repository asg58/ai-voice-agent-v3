from memory.memory_manager import MemoryManager

class PersistentMemory:
    def __init__(self, memory_manager: MemoryManager = None):
        self.memory_manager = memory_manager

    def save_data(self, key, value):
        """
        Sla belangrijke gegevens permanent op via MemoryManager (long_term).
        """
        if self.memory_manager:
            return self.memory_manager.save(key, value, type_="long_term")
        # Fallback mock
        with open("persistent_memory.json", "a") as file:
            file.write(f"{key}: {value}\n")

    def retrieve_data(self, key):
        """
        Haal opgeslagen gegevens op via MemoryManager (long_term).
        """
        if self.memory_manager:
            return self.memory_manager.get(key, type_="long_term")
        # Fallback mock
        return f"Data for {key}"
