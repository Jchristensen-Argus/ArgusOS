import ollama

from argus.identity import Identity


class AI:

    def __init__(self):
        self.identity = Identity()

    def chat(self, message):

        response = ollama.chat(
            model="llama3.1:8b",
            messages=[
                {
                    "role": "system",
                    "content": self.identity.system_prompt()
                },
                {
                    "role": "user",
                    "content": message
                }
            ]
        )

        return response["message"]["content"]