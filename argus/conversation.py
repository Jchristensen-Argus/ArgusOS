from argus.ai import AI
from argus.brain import Brain


class Conversation:

    def __init__(self):
        self.ai = AI()
        self.brain = Brain()

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

        decision = self.brain.think(message)

        if decision == "chat":
            reply = self.ai.chat(message)
        else:
            reply = "I'm not sure how to handle that yet."

        print("Argus >")
        print(reply)
        print()