"""
Application lifecycle for ArgusOS.

Purpose:
    Represent the running ArgusOS application: its services and its
    lifecycle (start / shutdown), per
    factory/packages/002_BOOTSTRAP.md.

Responsibilities:
    - Hold the application's service Container.
    - Expose start() and shutdown() lifecycle methods.
    - Report whether the application is currently running.

Non-Responsibilities:
    - The Application does not construct services. Construction and
      wiring happen in argus/bootstrap.py.
    - No engine logic (Atlas, Cortex, Hermes, Navigator, Sentinel) is
      implemented or invoked here; that is out of scope for Package 002.

Dependencies:
    Container. Resolves "logger" from the container for lifecycle
    logging.
"""

from argus.container import Container


class Application:
    """
    Represents the running ArgusOS application instance.

    Purpose:
        Own the application's lifecycle state and provide a single,
        well-defined place to start up and shut down.

    Responsibilities:
        - Track whether the application is running.
        - Log lifecycle transitions.

    Dependencies:
        Container (for resolving the logger).
    """

    def __init__(self, container: Container) -> None:
        self._container = container
        self._running = False

    @property
    def container(self) -> Container:
        """The application's dependency injection container."""
        return self._container

    @property
    def is_running(self) -> bool:
        """Whether the application is currently running."""
        return self._running

    def start(self) -> None:
        """Mark the application as running and log startup completion."""
        logger = self._container.resolve("logger")
        self._running = True
        logger.info("ArgusOS application started.")

    def shutdown(self) -> None:
        """
        Perform a graceful shutdown of the application.

        Safe to call even if the application was never started, or has
        already been shut down.
        """
        logger = self._container.resolve("logger")
        if self._running:
            logger.info("ArgusOS application shutting down.")
        self._running = False
