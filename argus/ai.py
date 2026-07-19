from argus.memory import Memory
import ollama

from argus.identity import Identity


class AI:

    def __init__(self):
        self.identity = Identity()
        self.memory = Memory()

    def memory_context(self):

        memories = self.memory.recall()

        if not memories:
            return "No stored memories."

        return "\n".join(f"- {memory}" for memory in memories)
    
    def chat(self, message):

        response = ollama.chat(
            model="llama3.1:8b",
           messages=[
    {
        "role": "system",
        "content":
            self.identity.system_prompt()
            + "\n\nKnown Memories:\n"
            + self.memory_context()
    },
    {
        "role": "user",
        "content": message
    }
]
        )

        return response["message"]["content"]