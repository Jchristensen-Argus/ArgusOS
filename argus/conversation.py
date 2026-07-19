class Conversation:

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

        if "hello" in message.lower() or "hi" in message.lower():
            print("Argus >")
            print("Hello, Joel. It's good to see you.\n")

        elif "how are you" in message.lower():
            print("Argus >")
            print("I'm doing great. Every version makes me a little smarter.\n")

        elif "who are you" in message.lower():
            print("Argus >")
            print("I'm Argus, your AI operating system. One day I'll help you run your businesses and organize your life.\n")

        else:
            print("Argus >")
            print("That's interesting. Soon a real AI model will answer instead of these scripted responses.\n")