class Identity:
    """
    The identity of Argus.

    This class contains information that defines
    who Argus is.
    """

    def __init__(self):
        self.name = "Argus"
        self.version = "0.0.1"
        self.codename = "The Spark"

    def introduce(self):
        return (
            f"{self.name} {self.version}\n"
            f"Codename: {self.codename}"
        )
    