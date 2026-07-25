"""
Bootstrap process for ArgusOS.

Purpose:
    Perform the startup sequence required to bring an ArgusOS
    Application to a running state, per
    factory/packages/002_BOOTSTRAP.md, factory/packages/003_EVENT_BUS.md,
    factory/packages/004_SERVICE_REGISTRY.md,
    factory/packages/005_SERVICE_LIFECYCLE.md,
    factory/packages/006_KNOWLEDGE_SERVICE.md,
    factory/packages/007_MEMORY_SERVICE.md,
    factory/packages/008_SCHEDULER_SERVICE.md,
    factory/packages/009_INTENT_ROUTER.md, and
    factory/packages/010_WORKFLOW_ENGINE.md.

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
    8. Construct the Memory Service (depends on the Event Bus) and
       register it with the Container, per Package 007. Bootstrap is
       the only place that constructs JSONMemoryStorage and
       MemoryService directly; every other subsystem must resolve
       MemoryService from the Container.
    9. Construct the Scheduler (depends on the Event Bus) and register
       it with the Container, per Package 008. Bootstrap is the only
       place that constructs Scheduler directly; every other subsystem
       must resolve it from the Container. Scheduler is registered
       only (LifecycleState.REGISTERED) here, exactly like every other
       core service - its own initialize()/start() are deliberately
       NOT called by this package (see Package 008's engineering
       notes and ADR-0002): calling them here would exercise
       Scheduler's IService lifecycle without a corresponding,
       necessarily-paired call into the Lifecycle Manager, which is
       precisely the divergence risk ADR-0002 identified. Nothing in
       this package requires Scheduler to be started; tick() is never
       called automatically (v1 has no background thread), so there is
       no behavioral need to start it during bootstrap.
    10. Construct the Intent Router (depends on the Event Bus) and
        register it with the Container, per Package 009. Bootstrap is
        the only place that constructs IntentRouter directly; every
        other subsystem must resolve it from the Container. Like
        Scheduler, IntentRouter implements IService but is registered
        only (LifecycleState.REGISTERED) here - its own
        initialize()/start() are deliberately NOT called by this
        package, for the same divergence-avoidance reasoning recorded
        in ADR-0002 and already applied to Scheduler in step 9.
        IntentRouter is a second data point for that ADR: unlike
        Scheduler's tick(), none of IntentRouter's parse()/route()/
        register_handler() are gated by lifecycle state at all, so
        bootstrap's abstention from starting it has no behavioral
        consequence either way.
    11. Construct the Workflow Engine (depends on the Event Bus) and
        register it with the Container, per Package 010. Bootstrap is
        the only place that constructs WorkflowEngine directly; every
        other subsystem must resolve it from the Container. Like
        Scheduler and IntentRouter, WorkflowEngine implements IService
        but is registered only (LifecycleState.REGISTERED) here - its
        own initialize()/start() are deliberately NOT called by this
        package, for the same divergence-avoidance reasoning recorded
        in ADR-0002. Unlike IntentRouter, WorkflowEngine's execute()
        genuinely requires the engine's own state to be RUNNING (see
        Package 010's engineering notes) - meaning a caller must call
        engine.initialize()/start() directly before execute() will
        work at all, exactly as Scheduler's tick() requires
        scheduler.initialize()/start() before it will run anything.
        Bootstrap does not do this itself, for the same reason it
        does not for Scheduler.
    12. Register the ten core services (Configuration, Logger, Event
        Bus, Service Registry, Lifecycle Manager, Knowledge Service,
        Memory Service, Scheduler, Intent Router, Workflow Engine) in
        the Service Registry (identity/descriptive data only) and in
        the Lifecycle Manager, where each enters
        LifecycleState.REGISTERED. None of them are initialized or
        started by this package.
    13. Construct and start the Application.

Scope:
    This module implements only application startup infrastructure.
    No engines (Atlas, Cortex, Hermes, Navigator, Sentinel) are
    initialized here. Packages 003-010 register the Event Bus, Service
    Registry, Lifecycle Manager, Knowledge Service, Memory Service,
    Scheduler, Intent Router, and Workflow Engine respectively but do
    not change Application's lifecycle: no lifecycle events are
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
    KnowledgeService), argus.memory (JSONMemoryStorage, MemoryService),
    argus.scheduler (Scheduler).
"""

from argus.application import Application
from argus.configuration import Configuration
from argus.container import Container
from argus.events import IEventBus, InMemoryEventBus
from argus.intent import IIntentRouter, IntentRouter
from argus.knowledge import IKnowledgeService, JSONKnowledgeStorage, KnowledgeService
from argus.lifecycle import LifecycleManager
from argus.logging_service import get_logger, initialize_logging
from argus.memory import IMemoryService, JSONMemoryStorage, MemoryService
from argus.scheduler import IScheduler, Scheduler
from argus.workflow import IWorkflowEngine, WorkflowEngine
from argus.services import IServiceRegistry, InMemoryServiceRegistry, ServiceDescriptor

# The ArgusOS release this package targets, per the Package 010 work
# order header ("ArgusOS Version Target: v0.0.10"). Used as the
# version recorded on every core ServiceDescriptor registered during
# bootstrap.
CORE_SERVICES_VERSION = "0.0.10"


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

    memory_storage = JSONMemoryStorage()
    memory_service = MemoryService(storage=memory_storage, event_bus=event_bus)
    container.register("memory_service", memory_service)

    scheduler = Scheduler(event_bus=event_bus)
    container.register("scheduler", scheduler)

    intent_router = IntentRouter(event_bus=event_bus)
    container.register("intent_router", intent_router)

    workflow_engine = WorkflowEngine(event_bus=event_bus)
    container.register("workflow_engine", workflow_engine)

    _register_core_services(
        service_registry=service_registry,
        lifecycle_manager=lifecycle_manager,
        configuration=configuration,
        logger=logger,
        event_bus=event_bus,
        knowledge_service=knowledge_service,
        memory_service=memory_service,
        scheduler=scheduler,
        intent_router=intent_router,
        workflow_engine=workflow_engine,
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
    memory_service: IMemoryService,
    scheduler: IScheduler,
    intent_router: IIntentRouter,
    workflow_engine: IWorkflowEngine,
) -> None:
    """
    Register the kernel's own core services with the Service Registry
    and the Lifecycle Manager, per Package 005's Bootstrap Integration
    (as amended by the Package 005 architectural revision), Package
    006's "KnowledgeService becomes a Core Service" requirement, and
    the equivalent requirement for the Memory Service (Package 007),
    Scheduler (Package 008), the Intent Router (Package 009), and the
    Workflow Engine (Package 010).

    Each of Configuration, the Logger, the Event Bus, the Service
    Registry, the Lifecycle Manager, the Knowledge Service, the Memory
    Service, Scheduler, the Intent Router, and the Workflow Engine is
    recorded as a ServiceDescriptor (identity and descriptive data
    only, no runtime state) in the Service Registry, and as a
    LifecycleState.REGISTERED entry in the Lifecycle Manager, which is
    the sole owner of runtime lifecycle state for the Lifecycle
    Manager's own purposes. Neither initialize() nor start() is called
    on the Lifecycle Manager for any of them here. Scheduler, the
    Intent Router, and the Workflow Engine are the three classes among
    these ten that actually implement IService (see ADR-0002), but
    this function still does not call any of their initialize()/
    start() directly - see the Startup Sequence note in this module's
    docstring for why exercising their real IService lifecycles during
    bootstrap was deliberately avoided.

    Parameters:
        service_registry: Where each core service is recorded as a
            ServiceDescriptor.
        lifecycle_manager: Where each core service's name is
            registered as LifecycleState.REGISTERED.
        configuration: The loaded Configuration instance.
        logger: The application logger.
        event_bus: The Event Bus instance.
        knowledge_service: The Knowledge Service instance.
        memory_service: The Memory Service instance.
        scheduler: The Scheduler instance.
        intent_router: The Intent Router instance.
        workflow_engine: The Workflow Engine instance.
    """
    core_services = (
        ("configuration", configuration, type(configuration)),
        ("logger", logger, type(logger)),
        ("event_bus", event_bus, IEventBus),
        ("service_registry", service_registry, IServiceRegistry),
        ("lifecycle_manager", lifecycle_manager, type(lifecycle_manager)),
        ("knowledge_service", knowledge_service, IKnowledgeService),
        ("memory_service", memory_service, IMemoryService),
        ("scheduler", scheduler, IScheduler),
        ("intent_router", intent_router, IIntentRouter),
        ("workflow_engine", workflow_engine, IWorkflowEngine),
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
