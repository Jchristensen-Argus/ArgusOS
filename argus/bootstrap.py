"""
Bootstrap process for ArgusOS.

Purpose:
    Perform the startup sequence required to bring an ArgusOS
    Application to a running state, per
    factory/packages/002_BOOTSTRAP.md and
    factory/packages/003_EVENT_BUS.md.

Startup Sequence:
    1. Create the dependency injection Container.
    2. Load Configuration.
    3. Initialize logging (depends on Configuration, per
       design/specifications/LOGGING.md).
    4. Construct the Event Bus (depends on logging) and register it
       against the IEventBus contract, per Package 003. Bootstrap is
       the only place that constructs InMemoryEventBus directly; every
       other subsystem must resolve it from the Container.
    5. Register core services with the Container.
    6. Construct and start the Application.

Scope:
    This module implements only application startup infrastructure.
    No engines (Atlas, Cortex, Hermes, Navigator, Sentinel) are
    initialized here. Package 003 registers the Event Bus but does not
    change Application's lifecycle: no lifecycle events are published
    automatically by this package (see Package 003 engineering notes).

Dependencies:
    Container, Configuration, logging_service, Application,
    argus.events (InMemoryEventBus).
"""

from argus.application import Application
from argus.configuration import Configuration
from argus.container import Container
from argus.events import InMemoryEventBus
from argus.logging_service import get_logger, initialize_logging


def bootstrap() -> Application:
    """
    Run the ArgusOS startup sequence and return a running Application.

    Returns:
        A started Application instance, ready for use.
    """
    container = Container()

    configuration = Configuration.load()
    container.register("configuration", configuration)

    logger = initialize_logging(configuration)
    container.register("logger", logger)

    event_bus = InMemoryEventBus(logger=get_logger("event_bus"))
    container.register("event_bus", event_bus)

    application = Application(container)
    application.start()

    return application
