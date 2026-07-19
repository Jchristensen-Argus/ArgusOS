class Brain:
    """
    The Brain decides what Argus should do next.

    It does not generate responses.
    It routes requests to the appropriate subsystem.
    """

    def think(self, message):
        """
        Analyze the user's message and determine the intent.

        Future intents may include:
        - chat
        - remember
        - forget
        - project
        - quote
        - email
        - agent

        For now, everything is treated as normal chat.
        """

        return "chat"