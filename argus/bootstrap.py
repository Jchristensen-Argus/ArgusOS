"""
Bootstrap process for ArgusOS.

Purpose:
    Perform the startup sequence required to bring an ArgusOS
    Application to a running state, per
    factory/packages/002_BOOTSTRAP.md, factory/packages/003_EVENT_BUS.md,
    factory/packages/004_SERVICE_REGISTRY.md,
    factory/packages/005_SERVICE_LIFECYCLE.md, and
    factory/packages/006_KNOWLEDGE_SERVICE.md.

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
    6. Construct the Lifecycle Manager and register it with the
       Container, per Package 005.
    7. Construct the Knowledge Service (depends on the Event Bus) and
       register it with the Container, per Package 006. Bootstrap is
       the only place that constructs JSONKnowledgeStorage and
       KnowledgeService directly; every other subsystem must resolve
       KnowledgeService from the Container.
    8. Register the six core services (Configuration, Logger, Event
       Bus, Service Registry, Lifecycle Manager, Knowledge Service) in
       the Service Registry (identity/descriptive data only) and in
       the Lifecycle Manager, where each enters
       LifecycleState.REGISTERED. None of them are initialized or
       started by this package.
    9. Construct and start the Application.

Scope:
    This module implements only application startup infrastructure.
    No engines (Atlas, Cortex, Hermes, Navigator, Sentinel) are
    initialized here. Packages 003-006 register the Event Bus, Service
    Registry, Lifecycle Manager, and Knowledge Service respectively but
    do not change Application's lifecycle: no lifecycle events are
    published, and no core service is initialized or started, by this
    package (see the Package 005 engineering notes).

Architectural Revision (Package 005):
    ServiceDescriptor no longer carries a `state` field. Architecture
    review found that ServiceDescriptor.state (Package 004's
    ServiceState) and the Lifecycle Manager's LifecycleState (Package
    005) were two unsynchronized models of the same concept. The
    Lifecycle Manager is now the sole owner of runtime lifecycle
    state; the Service Registry holds only identity and descriptive
    data. See argus/services/service_descriptor.py.

Dependencies:
    Container, Configuration, logging_service, Application,
    argus.events (InMemoryEventBus), argus.services
    (InMemoryServiceRegistry, ServiceDescriptor), argus.lifecycle
    (LifecycleManager), argus.knowledge (JSONKnowledgeStorage,
    KnowledgeService).
"""

from argus.application import Application
from argus.configuration import Configuration
from argus.container import Container
from argus.events import IEventBus, InMemoryEventBus
from argus.knowledge import IKnowledgeService, JSONKnowledgeStorage, KnowledgeService
from argus.lifecycle import LifecycleManager
from argus.logging_service import get_logger, initialize_logging
from argus.services import IServiceRegistry, InMemoryServiceRegistry, ServiceDescriptor

# The ArgusOS release this package targets, per the Package 006 work
# order header ("ArgusOS Version Target: v0.0.6"). Used as the version
# recorded on every core ServiceDescriptor registered during bootstrap.
CORE_SERVICES_VERSION = "0.0.6"


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

    lifecycle_manager = LifecycleManager()
    container.register("lifecycle_manager", lifecycle_manager)

    knowledge_storage = JSONKnowledgeStorage()
    knowledge_service = KnowledgeService(storage=knowledge_storage, event_bus=event_bus)
    container.register("knowledge_service", knowledge_service)

    _register_core_services(
        service_registry=service_registry,
        lifecycle_manager=lifecycle_manager,
        configuration=configuration,
        logger=logger,
        event_bus=event_bus,
        knowledge_service=knowledge_service,
    )

    application = Application(container)
    application.start()

    return application


def _register_core_services(
    *,
    service_registry: IServiceRegistry,
    lifecycle_manager: LifecycleManager,
    configuration: Configuration,
    logger,
    event_bus: IEventBus,
    knowledge_service: IKnowledgeService,
) -> None:
    """
    Register the kernel's own core services with the Service Registry
    and the Lifecycle Manager, per Package 005's Bootstrap Integration
    (as amended by the Package 005 architectural revision) and Package
    006's "KnowledgeService becomes a Core Service" requirement.

    Each of Configuration, the Logger, the Event Bus, the Service
    Registry, the Lifecycle Manager, and the Knowledge Service is
    recorded as a ServiceDescriptor (identity and descriptive data
    only, no runtime state) in the Service Registry, and as a
    LifecycleState.REGISTERED entry in the Lifecycle Manager, which is
    the sole owner of runtime lifecycle state. Neither initialize()
    nor start() is called on the Lifecycle Manager for any of them:
    none of these six classes implements IService yet, and no package
    to date requires (or permits) automatically initializing or
    starting core services during bootstrap.

    Parameters:
        service_registry: Where each core service is recorded as a
            ServiceDescriptor.
        lifecycle_manager: Where each core service's name is
            registered as LifecycleState.REGISTERED.
        configuration: The loaded Configuration instance.
        logger: The application logger.
        event_bus: The Event Bus instance.
        knowledge_service: The Knowledge Service instance.
    """
    core_services = (
        ("configuration", configuration, type(configuration)),
        ("logger", logger, type(logger)),
        ("event_bus", event_bus, IEventBus),
        ("service_registry", service_registry, IServiceRegistry),
        ("lifecycle_manager", lifecycle_manager, type(lifecycle_manager)),
        ("knowledge_service", knowledge_service, IKnowledgeService),
    )

    for name, instance, interface in core_services:
        service_registry.register(
            ServiceDescriptor(
                name=name,
                instance=instance,
                interface=interface,
                version=CORE_SERVICES_VERSION,
            )
        )
        lifecycle_manager.register(name)
