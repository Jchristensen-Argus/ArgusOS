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
    factory/packages/009_INTENT_ROUTER.md,
    factory/packages/010_WORKFLOW_ENGINE.md,
    factory/packages/011_CONVERSATION_MANAGER.md,
    factory/packages/012_INTENT_DISPATCHER.md, and
    factory/packages/013_CAPABILITY_REGISTRY.md.

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
    12. Construct the Conversation Manager (depends on the Event Bus,
        the Intent Router, and the Workflow Engine) and register it
        with the Container, per Package 011. Bootstrap is the only
        place that constructs ConversationManager directly; every
        other subsystem must resolve it from the Container. Like
        Scheduler and WorkflowEngine, ConversationManager implements
        IService with a genuine gate: receive() requires the
        manager's own state to be RUNNING, exactly as tick() and
        execute() do. Registered only (LifecycleState.REGISTERED)
        here, for the same divergence-avoidance reasoning recorded in
        ADR-0002.
    13. Construct the Capability Registry (depends on the Event Bus)
        and register it with the Container, per Package 013.
        Bootstrap is the only place that constructs CapabilityRegistry
        directly; every other subsystem must resolve it from the
        Container. Immediately after construction, bootstrap.py
        registers five Capability instances - one per
        argus.dispatcher.mapping.DEFAULT_WORKFLOW_IDS entry, the same
        table Package 012 used - as this package's Version 1
        population, per its explicit "Populate Version 1 using the
        existing workflow mappings introduced in Package 012"
        requirement. Unlike Scheduler, IntentRouter, WorkflowEngine,
        ConversationManager, and IntentDispatcher, CapabilityRegistry
        does NOT implement IService - see
        argus/capability/interfaces.py's Architectural Note and
        ADR-0002's newly appended Empirical Finding for this package.
        It is registered with the Lifecycle Manager as
        LifecycleState.REGISTERED, exactly like Knowledge Service and
        Memory Service, which is not a divergence-avoidance workaround
        here (there is no IService lifecycle to diverge from) but
        simply this service's natural, permanent state.
    14. Construct the Intent Dispatcher (depends on the Event Bus and,
        as of Package 013, the Capability Registry) and register it
        with the Container, per Packages 012 and 013. Bootstrap is the
        only place that constructs IntentDispatcher directly; every
        other subsystem must resolve it from the Container. As of
        Package 013, IntentDispatcher no longer depends on the
        Workflow Engine directly, nor does it hold any capability
        knowledge of its own - see
        argus/dispatcher/dispatcher.py's module docstring. Instead,
        bootstrap.py builds a single `action_factory` callable via
        `functools.partial(build_action_from_capability,
        workflow_engine=workflow_engine)` and injects it into
        IntentDispatcher alongside the Capability Registry - this
        closure is the only place in this package where a
        WorkflowAction is ever actually constructed (lazily, once per
        dispatch() call, inside build_action_from_capability - see
        argus/dispatcher/action.py). Like Scheduler, IntentRouter,
        WorkflowEngine, and Conversation Manager, IntentDispatcher
        implements IService with a genuine gate (dispatch() requires
        the dispatcher's own state to be RUNNING) but is registered
        only (LifecycleState.REGISTERED) here, for the same
        divergence-avoidance reasoning recorded in ADR-0002.
    15. Register the thirteen core services (Configuration, Logger,
        Event Bus, Service Registry, Lifecycle Manager, Knowledge
        Service, Memory Service, Scheduler, Intent Router, Workflow
        Engine, Conversation Manager, Capability Registry, Intent
        Dispatcher) in the Service Registry (identity/descriptive data
        only) and in the Lifecycle Manager, where each enters
        LifecycleState.REGISTERED. None of them are initialized or
        started by this package.
    16. Construct and start the Application.

Scope:
    This module implements only application startup infrastructure.
    No engines (Atlas, Cortex, Hermes, Navigator, Sentinel) are
    initialized here. Packages 003-013 register the Event Bus, Service
    Registry, Lifecycle Manager, Knowledge Service, Memory Service,
    Scheduler, Intent Router, Workflow Engine, Conversation Manager,
    Capability Registry, and Intent Dispatcher respectively but do not
    change Application's lifecycle: no lifecycle events are published,
    and no core service is initialized or started, by this package
    (see the Package 005 engineering notes).

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

import functools

from argus.application import Application
from argus.capability import Capability, ICapabilityRegistry, CapabilityRegistry
from argus.configuration import Configuration
from argus.container import Container
from argus.conversation import IConversationManager, ConversationManager
from argus.dispatcher import (
    DEFAULT_WORKFLOW_IDS,
    IIntentDispatcher,
    IntentDispatcher,
    WorkflowAction,
    build_action_from_capability,
)
from argus.events import IEventBus, InMemoryEventBus
from argus.intent import IIntentRouter, IntentRouter
from argus.knowledge import IKnowledgeService, JSONKnowledgeStorage, KnowledgeService
from argus.lifecycle import LifecycleManager
from argus.logging_service import get_logger, initialize_logging
from argus.memory import IMemoryService, JSONMemoryStorage, MemoryService
from argus.scheduler import IScheduler, Scheduler
from argus.workflow import IWorkflowEngine, WorkflowEngine
from argus.services import IServiceRegistry, InMemoryServiceRegistry, ServiceDescriptor

# The currently released ArgusOS version.
#
# This constant always matches the latest released Git tag and represents
# the version of the repository currently checked into source control.
#
# It is NOT advanced during package implementation.
#
# It is updated only as part of the official release process after:
#   • Integration
#   • Full regression testing
#   • Smoke testing
#   • Git commit
#   • Git tag
#
# Every core ServiceDescriptor registered during bootstrap uses this value.
CORE_SERVICES_VERSION = "0.1.2"


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

    conversation_manager = ConversationManager(
        event_bus=event_bus,
        intent_router=intent_router,
        workflow_engine=workflow_engine,
    )
    container.register("conversation_manager", conversation_manager)

    capability_registry = CapabilityRegistry(event_bus=event_bus)
    for intent_type, workflow_id in DEFAULT_WORKFLOW_IDS.items():
        capability_registry.register(
            Capability(
                name=f"{intent_type.name.title()} Capability",
                description=(
                    f"Handles {intent_type.name} intents by delegating to "
                    f"the {workflow_id!r} workflow."
                ),
                intent_types=(intent_type,),
                action_kind=WorkflowAction.kind,
                workflow_id=workflow_id,
            )
        )
    container.register("capability_registry", capability_registry)

    intent_dispatcher = IntentDispatcher(
        event_bus=event_bus,
        capability_registry=capability_registry,
        action_factory=functools.partial(
            build_action_from_capability, workflow_engine=workflow_engine
        ),
    )
    container.register("intent_dispatcher", intent_dispatcher)

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
        conversation_manager=conversation_manager,
        capability_registry=capability_registry,
        intent_dispatcher=intent_dispatcher,
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
    conversation_manager: IConversationManager,
    capability_registry: ICapabilityRegistry,
    intent_dispatcher: IIntentDispatcher,
) -> None:
    """
    Register the kernel's own core services with the Service Registry
    and the Lifecycle Manager, per Package 005's Bootstrap Integration
    (as amended by the Package 005 architectural revision), Package
    006's "KnowledgeService becomes a Core Service" requirement, and
    the equivalent requirement for the Memory Service (Package 007),
    Scheduler (Package 008), the Intent Router (Package 009), the
    Workflow Engine (Package 010), and the Conversation Manager
    (Package 011).

    Each of Configuration, the Logger, the Event Bus, the Service
    Registry, the Lifecycle Manager, the Knowledge Service, the Memory
    Service, Scheduler, the Intent Router, the Workflow Engine, the
    Conversation Manager, the Capability Registry, and the Intent
    Dispatcher is recorded as a ServiceDescriptor (identity and
    descriptive data only, no runtime state) in the Service Registry,
    and as a LifecycleState.REGISTERED entry in the Lifecycle Manager,
    which is the sole owner of runtime lifecycle state for the
    Lifecycle Manager's own purposes. Neither initialize() nor start()
    is called on the Lifecycle Manager for any of them here. Scheduler,
    the Intent Router, the Workflow Engine, the Conversation Manager,
    and the Intent Dispatcher are five of these thirteen that actually
    implement IService (see ADR-0002); the Capability Registry
    deliberately does not (see
    argus/capability/interfaces.py's Architectural Note). This
    function still does not call any IService adopter's
    initialize()/start() directly - see the Startup Sequence note in
    this module's docstring for why exercising their real IService
    lifecycles during bootstrap was deliberately avoided.

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
        conversation_manager: The Conversation Manager instance.
        capability_registry: The Capability Registry instance.
        intent_dispatcher: The Intent Dispatcher instance.
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
        ("conversation_manager", conversation_manager, IConversationManager),
        ("capability_registry", capability_registry, ICapabilityRegistry),
        ("intent_dispatcher", intent_dispatcher, IIntentDispatcher),
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
