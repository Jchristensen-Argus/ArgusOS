import json
from pathlib import Path


class Memory:

    def __init__(self):

        self.memory_file = Path("memory/memories.json")
        self.memories = self.load()

    def save(self):
        with open(self.memory_file, "w") as file:
            json.dump(self.memories, file, indent=4)

    def load(self):

        with open(self.memory_file, "r") as file:
            return json.load(file)
        
    def remember(self, text):

        self.memories.append(text)
        self.save()    