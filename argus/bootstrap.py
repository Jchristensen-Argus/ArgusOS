"""
Bootstrap process for ArgusOS.

Purpose:
    Perform the startup sequence required to bring an ArgusOS
    Application to a running state, per
    factory/packages/002_BOOTSTRAP.md, factory/packages/003_EVENT_BUS.md,
    and factory/packages/004_SERVICE_REGISTRY.md.

Startup Sequence:
    1. Create the dependency injection Container.
    2. Load Configuration.
    3. Initialize logging (depends on Configuration, per
       design/specifications/LOGGING.md).
    4. Construct the Event Bus (depends on logging) and register it
       against the IEventBus contract, per Package 003. Bootstrap is
       the only place that constructs InMemoryEventBus directly; every
       other subsystem must resolve it from the Container.
    5. Construct the Service Registry and register it against the
       IServiceRegistry contract, per Package 004. Bootstrap is the
       only place that constructs InMemoryServiceRegistry directly;
       every other subsystem must resolve it from the Container.
    6. Register core services with the Container.
    7. Construct and start the Application.

Scope:
    This module implements only application startup infrastructure.
    No engines (Atlas, Cortex, Hermes, Navigator, Sentinel) are
    initialized here. Packages 003 and 004 register the Event Bus and
    Service Registry respectively but do not change Application's
    lifecycle: no lifecycle events are published and no services are
    auto-registered into the Service Registry by this package (see
    Package 004 engineering notes).

Dependencies:
    Container, Configuration, logging_service, Application,
    argus.events (InMemoryEventBus), argus.services
    (InMemoryServiceRegistry).
"""

from argus.application import Application
from argus.configuration import Configuration
from argus.container import Container
from argus.events import InMemoryEventBus
from argus.logging_service import get_logger, initialize_logging
from argus.services import InMemoryServiceRegistry


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

    service_registry = InMemoryServiceRegistry()
    container.register("service_registry", service_registry)

    application = Application(container)
    application.start()

    return application
