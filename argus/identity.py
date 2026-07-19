from pathlib import Path


class Identity:

    def __init__(self):
        self.prompt_file = Path("config/system_prompt.md")

    def introduce(self):
        return "Argus AI Operating System"

    def system_prompt(self):
        with open(self.prompt_file, "r", encoding="utf-8") as file:
            return file.read()