import ollama


class AI:

    def chat(self, message):

        response = ollama.chat(
            model="llama3.1:8b",
            messages=[
                {
                    "role": "user",
                    "content": message
                }
            ]
        )

        return response["message"]["content"]