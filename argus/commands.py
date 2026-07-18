import os


class CommandManager:
    def __init__(self, identity):
        self.identity = identity

    def execute(self, command):
        if command == "help":
            self.help()

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
identity
version
status
clear
quit
""")