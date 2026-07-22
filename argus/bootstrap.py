"""
Bootstrap process for ArgusOS.

Purpose:
    Perform the startup sequence required to bring an ArgusOS
    Application to a running state, per
    factory/packages/002_BOOTSTRAP.md.

Startup Sequence:
    1. Create the dependency injection Container.
    2. Load Configuration.
    3. Initialize logging (depends on Configuration, per
       design/specifications/LOGGING.md).
    4. Register core services with the Container.
    5. Construct and start the Application.

Scope:
    This module implements only application startup infrastructure.
    No engines (Atlas, Cortex, Hermes, Navigator, Sentinel) and no
    Event Bus are initialized here; those are explicitly out of scope
    for Package 002 - Bootstrap.

Dependencies:
    Container, Configuration, logging_service, Application.
"""

from argus.application import Application
from argus.configuration import Configuration
from argus.container import Container
from argus.logging_service import initialize_logging


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

    application = Application(container)
    application.start()

    return application
