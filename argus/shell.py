from argus.identity import Identity
from argus.commands import CommandManager


class Shell:
    def __init__(self):
        self.identity = Identity()
        self.commands = CommandManager(self.identity)

    def start(self):
        print("=" * 60)
        print(self.identity.introduce())
        print("=" * 60)

        print("\nWelcome back, Joel!")
        print("Type 'help' for available commands.\n")

        while True:
            command = input("Argus > ").strip().lower()

            if not self.commands.execute(command):
                break