import os
from argus.memory import Memory
from argus.conversation import Conversation


class CommandManager:
    def __init__(self, identity):
        self.identity = identity
        self.conversation = Conversation()
        self.memory = Memory()

    def execute(self, command):
        if command == "help":
            self.help()

        elif command == "memories":

            memories = self.memory.recall()

            if not memories:
                print("\nI don't have any memories yet.\n")
        
            else:
                print("\nMemories:\n")
            
                for i, memory in enumerate(memories, start=1):
                    print(f"{i}. {memory}")

            print()
        
        elif command == "remember":
            text = input("\nWhat would you like me to remember?\n> ")
            self.memory.remember(text)
            print("\nMemory stored.\n")
        
        elif command == "identity":
            print()
            print(self.identity.introduce())
            print()

        elif command == "version":
            print(f"\nVersion: {self.identity.version}\n")

        elif command == "status":
            print("\nArgus is online and ready.\n")

        elif command == "clear":
            os.system("cls" if os.name == "nt" else "clear")

        elif command == "chat":
            self.conversation.start()

        elif command in ("quit", "exit"):
            print("\nGoodbye, Joel.")
            return False

        elif command == "":
            pass

        else:
            print(f"\nUnknown command: {command}\n")

        return True

    def help(self):
        print("""
Available Commands
------------------
help
remember
memories            
identity
version
status
clear
quit
""")