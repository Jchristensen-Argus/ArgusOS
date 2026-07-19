class Brain:
    """
    The Brain decides what Argus should do.

    It never performs the work itself.
    It only identifies the user's intent.
    """

    def think(self, message):

        text = message.lower().strip()

        if text.startswith("remember"):
            return "remember"

        if text in [
            "memories",
            "what do you remember",
            "show my memories"
        ]:
            return "memories"

        return "chat"