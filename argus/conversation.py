from argus.ai import AI
from argus.brain import Brain
from argus.memory import Memory


class Conversation:

    def __init__(self):
        self.ai = AI()
        self.brain = Brain()
        self.memory = Memory()

    def start(self):
        print("\n" + "=" * 60)
        print("Conversation Mode")
        print("=" * 60)

        print("\nHello Joel!")
        print("I'm Argus.")
        print("Right now I'm running in conversation mode.")
        print("Soon this will be powered by a local AI model.\n")

        print("Type 'exit' to return.\n")

        while True:

            user = input("You > ")

            if user.lower() == "exit":
                print("\nLeaving conversation mode.\n")
                break

            self.respond(user)

    def respond(self, message):

        print()

        intent = self.brain.think(message)

        if intent == "remember":

            memory = message[len("remember"):].strip()

            if memory:
                self.memory.remember(memory)
                reply = f"I'll remember that: {memory}"
            else:
                reply = "What would you like me to remember?"

        elif intent == "memories":

            memories = self.memory.recall()

            if memories:

                reply = "Here's what I remember:\n\n"

                for i, memory in enumerate(memories, start=1):
                    reply += f"{i}. {memory}\n"

            else:
                reply = "I don't have any memories yet."

        else:

            reply = self.ai.chat(message)

        print("Argus >")
        print(reply)
        print()