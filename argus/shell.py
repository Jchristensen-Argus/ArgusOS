from argus.identity import Identity


class Shell:
    def __init__(self):
        self.identity = Identity()

    def start(self):
        print("=" * 60)
        print(self.identity.introduce())
        print("=" * 60)

        print("\nWelcome back, Joel!")
        print("Type 'help' for available commands.\n")

        while True:
            command = input("Argus > ").strip().lower()

            if command == "help":
                self.show_help()

            elif command == "identity":
                print()
                print(self.identity.introduce())
                print()

            elif command == "version":
                print(f"\nVersion: {self.identity.version}\n")

            elif command in ("quit", "exit"):
                print("\nGoodbye, Joel.")
                break

            elif command == "":
                continue

            else:
                print(f"\nUnknown command: {command}\n")

    def show_help(self):
        print("""
Available Commands
------------------
help       Show this menu
identity   Display Argus identity
version    Display current version
quit       Exit Argus
""")