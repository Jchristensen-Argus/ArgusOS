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
    factory/packages/012_INTENT_DISPATCHER.md,
    factory/packages/013_CAPABILITY_REGISTRY.md,
    factory/packages/014_PLUGIN_MANAGER.md,
    factory/packages/015_PLANNER.md,
    factory/packages/016_AGENT_RUNTIME.md,
    factory/packages/017_CONNECTOR_FRAMEWORK.md,
    factory/packages/018_KNOWLEDGE_GRAPH.md,
    factory/packages/019_MEMORY_INTEGRATION.md,
    factory/packages/020_REASONING_ENGINE.md,
    factory/packages/021_DECISION_ENGINE.md,
    factory/packages/025_COGNITIVE_PIPELINE.md,
    factory/packages/026_AGENT_SESSION.md,
    factory/packages/027_RESPONSE_ENGINE.md, and
    factory/packages/032_EXECUTION_ENGINE.md.

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
    14. Construct the Plugin Manager (depends on the Event Bus) and
        register it with the Container, per Package 014. Bootstrap is
        the only place that constructs PluginManager directly; every
        other subsystem must resolve it from the Container.
        Immediately after construction, bootstrap.py registers one
        built-in Plugin - "Core Workflows" - whose exported_capabilities
        are the same five Capability instances already registered with
        the Capability Registry in step 13 (the identical objects, not
        copies), per this package's "Provide one or more built-in
        plugins representing the existing workflow implementations"
        requirement. This does not register anything a second time
        with the Capability Registry - PluginManager.register() only
        stores the Plugin and its capability references in
        PluginManager's own table; it never calls
        ICapabilityRegistry.register(). Unlike Scheduler, IntentRouter,
        WorkflowEngine, ConversationManager, and IntentDispatcher,
        PluginManager does NOT implement IService - see
        argus/plugins/interfaces.py's Architectural Note and
        ADR-0002's newly appended Empirical Finding for this package.
        It is registered with the Lifecycle Manager as
        LifecycleState.REGISTERED, exactly like Knowledge Service,
        Memory Service, and CapabilityRegistry.
    15. Construct the Intent Dispatcher (depends on the Event Bus and,
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
    16. Construct the Planner (depends on the Event Bus and the
        Capability Registry) and register it with the Container, per
        Package 015. Bootstrap is the only place that constructs
        Planner directly; every other subsystem must resolve it from
        the Container. Constructed last among the fifteen core
        services, immediately after the Intent Dispatcher, even
        though the target architecture diagram places the Planner
        conceptually *above* Intent and the Capability Registry -
        construction order here reflects dependency order only
        (Planner needs a live ICapabilityRegistry reference), not the
        diagram's own top-to-bottom reading, the same distinction
        already drawn for Capability Registry/Intent Dispatcher in
        Package 013. Planner's only touchpoint with the Capability
        Registry is a read-only `contains()` existence check inside
        validate_plan() - it never calls `register()`, `get()`, or
        `find_by_intent_type()`, and it has no dependency anywhere on
        argus.dispatcher, argus.workflow, or argus.plugins, per this
        package's explicit Objective and Plugin Integration guidance.
        Unlike Scheduler, IntentRouter, WorkflowEngine,
        ConversationManager, and IntentDispatcher, Planner does NOT
        implement IService - see argus/planner/interfaces.py's
        Architectural Note and ADR-0002's newly appended Empirical
        Finding for this package. It is registered with the Lifecycle
        Manager as LifecycleState.REGISTERED, exactly like Knowledge
        Service, Memory Service, CapabilityRegistry, and PluginManager.
    17. Construct the Knowledge Graph (depends on the Event Bus
        only) and register it with the Container, per Package 018.
        Bootstrap is the only place that constructs KnowledgeGraph
        directly; every other subsystem must resolve it from the
        Container. Constructed immediately after the Planner and
        immediately before the Agent Runtime, per the Bootstrap
        section's explicit construction order (Capability Registry ->
        Intent Dispatcher -> Planner -> Knowledge Graph -> Agent
        Runtime -> Connector Manager) - like Connector Manager's own
        placement (Package 017), this ordering is NOT dependency-
        driven: KnowledgeGraph has no functional dependency on the
        Capability Registry, Intent Dispatcher, Planner, Agent
        Runtime, or Connector Manager whatsoever - it depends only on
        the Event Bus, exactly like Scheduler, IntentRouter,
        CapabilityRegistry, and ConnectorManager. Unlike every prior
        purely-positional insertion, however, this one is inserted in
        the *middle* of the existing sequence rather than appended at
        the end - the Agent Runtime and Connector Manager's own
        construction, immediately below, is unchanged in every respect
        except now following the Knowledge Graph rather than the
        Planner directly. Nothing in this package modifies
        argus/planner/ or argus/runtime/ - "The Planner may consult
        the Knowledge Graph" (this package's own Architectural
        Position) describes a capability the target architecture now
        permits for a *future* package, not a requirement to wire the
        Planner to the Knowledge Graph in this one; see
        argus/knowledge_graph/graph.py's module docstring and
        factory/packages/018_KNOWLEDGE_GRAPH.md's Architectural
        Decisions for the full reasoning. Per its work order's
        explicit "Create: IKnowledgeGraph - Extend IService"
        instruction, KnowledgeGraph DOES implement IService - but
        unlike every genuinely-gated adopter, none of its own methods
        (add_entity/remove_entity/get_entity/list_entities/
        add_relationship/remove_relationship/list_relationships/
        neighbors/find_by_type) are gated on the RUNNING state,
        exactly mirroring IntentRouter's (Package 009) identical
        shape - see argus/knowledge_graph/interfaces.py's
        Architectural Note and ADR-0002's newly appended Empirical
        Finding for this package. It is registered only
        (LifecycleState.REGISTERED) here, like every other core
        service - its own initialize()/start() are deliberately NOT
        called by this package, for the same divergence-avoidance
        reasoning recorded in ADR-0002 and already applied to every
        prior IService adopter.
    18. Construct Memory Integration (depends on the Event Bus, the
        Memory Service, and the Knowledge Graph) and register it with
        the Container, per Package 019. Bootstrap is the only place
        that constructs MemoryIntegration directly; every other
        subsystem must resolve it from the Container. Constructed
        immediately after the Knowledge Graph and immediately before
        the Agent Runtime, per the Bootstrap section's explicit
        construction order (Capability Registry -> Intent Dispatcher
        -> Planner -> Knowledge Graph -> Memory Integration -> Agent
        Runtime -> Connector Manager) - unlike the Knowledge Graph's
        and Connector Manager's own purely-positional placements
        (Packages 017-018), this ordering IS dependency-driven:
        MemoryIntegration genuinely depends on a live IMemoryService
        reference (constructed at step 8) and a live IKnowledgeGraph
        reference (constructed immediately above, at step 17) -
        Memory Integration is "the only component responsible for
        translating memory records into graph entities and
        relationships," per this package's own Architectural
        Position, and cannot do that job without both. Per its work
        order's explicit "Create: IMemoryIntegration - Extend
        IService" instruction, MemoryIntegration DOES implement
        IService - and, unlike the Knowledge Graph (Package 018),
        applying ADR-0002's criterion independently to this package's
        own methods *would* have suggested adoption on its own:
        synchronize_memory()/synchronize_all()/remove_memory() each
        perform genuine, effectful cross-system coordination (reading
        IMemoryService, writing IKnowledgeGraph, in the same call) and
        are genuinely gated on the RUNNING state;
        synchronization_status()/reset() remain ungated, touching only
        this service's own internal bookkeeping - see
        argus/memory_integration/interfaces.py's Architectural Notes
        and ADR-0002's newly appended Empirical Finding for this
        package. Nothing in this package modifies argus/planner/ or
        argus/runtime/, per its own explicit Constraints. It is
        registered only (LifecycleState.REGISTERED) here, like every
        other core service - its own initialize()/start() are
        deliberately NOT called by this package, for the same
        divergence-avoidance reasoning recorded in ADR-0002 and
        already applied to every prior IService adopter.
    19. Construct the Reasoning Engine (depends on the Event Bus, the
        Knowledge Graph, and Memory Integration) and register it with
        the Container, per Package 020. Bootstrap is the only place
        that constructs ReasoningEngine directly; every other
        subsystem must resolve it from the Container. Constructed
        immediately after Memory Integration and immediately before
        the Agent Runtime, per the Bootstrap section's explicit
        construction order (Capability Registry -> Intent Dispatcher
        -> Planner -> Knowledge Graph -> Memory Integration ->
        Reasoning Engine -> Agent Runtime -> Connector Manager) - like
        Memory Integration's own placement (Package 019), this
        ordering IS dependency-driven: ReasoningEngine genuinely
        depends on a live IKnowledgeGraph reference (constructed at
        step 17) and a live IMemoryIntegration reference (constructed
        immediately above, at step 18) - "The Reasoning Engine
        consumes information from the Knowledge Graph and Memory
        Integration to produce structured reasoning results," per
        this package's own Objective, and cannot do that job without
        both (see argus/reasoning/engine.py's own Architectural
        Decision for exactly how the Memory Integration dependency is
        used: read-only, via synchronization_status(), attached as
        result metadata only). Per its work order's explicit "Create:
        IReasoningEngine - Extend IService" instruction, ReasoningEngine
        DOES implement IService - and, like the Knowledge Graph
        (Package 018) and unlike Memory Integration (Package 019),
        applying ADR-0002's criterion independently to this package's
        own methods would NOT have suggested adoption on its own: all
        six public methods (query()/neighbors()/find_paths()/
        related_entities()/entity_summary()/relationship_summary())
        are synchronous, read-only, in-memory operations with no
        method gated on the RUNNING state - see
        argus/reasoning/interfaces.py's Architectural Note and
        ADR-0002's newly appended Empirical Finding for this package.
        "The Planner should not consume the Reasoning Engine yet" -
        nothing in this package modifies argus/planner/ or
        argus/runtime/, per its own explicit Constraints. It is
        registered only (LifecycleState.REGISTERED) here, like every
        other core service - its own initialize()/start() are
        deliberately NOT called by this package, for the same
        divergence-avoidance reasoning recorded in ADR-0002 and
        already applied to every prior adopter.
    20. Construct the Decision Engine (depends on the Event Bus and
        the Reasoning Engine) and register it with the Container, per
        Package 021. Bootstrap is the only place that constructs
        DecisionEngine directly; every other subsystem must resolve
        it from the Container. Constructed immediately after the
        Reasoning Engine and immediately before the Agent Runtime, per
        the Bootstrap section's explicit construction order
        (Capability Registry -> Intent Dispatcher -> Planner ->
        Knowledge Graph -> Memory Integration -> Reasoning Engine ->
        Decision Engine -> Agent Runtime -> Connector Manager) - like
        Memory Integration's (Package 019) and the Reasoning Engine's
        (Package 020) own placements, this ordering IS
        dependency-driven: DecisionEngine genuinely depends on a live
        IReasoningEngine reference (constructed immediately above, at
        step 19) - the third consecutive dependency-driven core-
        service placement in this codebase. Unlike the Reasoning
        Engine's own genuine use of its injected IMemoryIntegration,
        however, DecisionEngine's injected IReasoningEngine is held
        but not called anywhere in this package's own Version 1
        implementation - see argus/decision/interfaces.py's own
        Architectural Note for the full reasoning (this package's
        Objective describes evaluate()/evaluate_all() operating on
        caller-supplied ReasoningResult objects directly, never on a
        live IReasoningEngine reference queried internally, and
        IReasoningEngine has no zero-argument whole-system snapshot
        method comparable to IMemoryIntegration.synchronization_status()
        for DecisionEngine to attach blindly). Per its work order's
        explicit "Create: IDecisionEngine - Extending IService"
        instruction, DecisionEngine DOES implement IService - and,
        like the Knowledge Graph (Package 018) and the Reasoning
        Engine (Package 020), and unlike Memory Integration (Package
        019), applying ADR-0002's criterion independently to this
        package's own methods would NOT have suggested adoption on
        its own: all six public methods (evaluate()/evaluate_all()/
        register_rule()/remove_rule()/list_rules()/decision_summary())
        are synchronous, in-memory operations with no method gated on
        the RUNNING state - see argus/decision/interfaces.py's
        Architectural Note and ADR-0002's newly appended Empirical
        Finding for this package. Nothing in this package modifies
        argus/planner/ or argus/runtime/, per its own explicit
        Constraints ("Planner shall remain unchanged"). It is
        registered only (LifecycleState.REGISTERED) here, like every
        other core service - its own initialize()/start() are
        deliberately NOT called by this package, for the same
        divergence-avoidance reasoning recorded in ADR-0002 and
        already applied to every prior adopter.
    21. Construct the Agent Runtime (depends on the Event Bus, the
        Intent Dispatcher, and the Planner) and register it with the
        Container, per Package 016. Bootstrap is the only place that
        constructs AgentRuntime directly; every other subsystem must
        resolve it from the Container. Constructed immediately after
        the Decision Engine (previously immediately after the
        Reasoning Engine, before Package 021 inserted the Decision
        Engine between them) - AgentRuntime's own dependencies are
        unchanged and still reflect dependency order only (Planner,
        not KnowledgeGraph, MemoryIntegration, ReasoningEngine, or
        DecisionEngine), not the target architecture diagram's
        top-to-bottom reading, the same distinction already drawn for
        Capability Registry/Intent Dispatcher (Package 013) and
        Planner/Intent Dispatcher (Package 015). AgentRuntime's only
        touchpoint with the Planner is a read-only get_plan() call
        inside start_execution(), used to confirm a given Plan's
        canonical status is VALIDATED - it never calls create_plan(),
        add_step(), remove_step(), reorder_steps(), or validate_plan().
        Every actual execution effect happens through exactly one
        call: the injected IIntentDispatcher's dispatch() - AgentRuntime
        has no dependency anywhere on argus.workflow, argus.plugins,
        argus.knowledge_graph, argus.memory_integration,
        argus.reasoning, or argus.decision ("The Runtime must not
        modify it," per Package 018's own Architectural Position, now
        also true of the bridge Package 019, the Reasoning Engine
        Package 020, and the Decision Engine Package 021 built on top
        of it). Unlike Capability Registry, Plugin Manager, and
        Planner (three consecutive non-adopters), AgentRuntime DOES
        implement IService, with start_execution()/resume_execution()
        genuinely gated on the runtime's own RUNNING state - see
        argus/runtime/interfaces.py's Architectural Note and
        ADR-0002's newly appended Empirical Finding for that package.
        Like every other IService adopter, it is registered only
        (LifecycleState.REGISTERED) here - its own initialize()/
        start() are deliberately NOT called by this package, for the
        same divergence-avoidance reasoning recorded in ADR-0002 and
        already applied to every prior adopter.
    22. Construct the Connector Manager (depends on the Event Bus
        only) and register it with the Container, per Package 017.
        Bootstrap is the only place that constructs ConnectorManager
        directly; every other subsystem must resolve it from the
        Container. Constructed immediately after the Agent Runtime,
        per the Bootstrap section's explicit construction order -
        like the Knowledge Graph's own placement (Package 018), this
        ordering is NOT dependency-driven: ConnectorManager has no
        functional dependency on the Capability Registry, Intent
        Dispatcher, Planner, Knowledge Graph, Memory Integration,
        Reasoning Engine, Decision Engine, or Agent Runtime whatsoever
        - it depends only on the Event Bus. Immediately after
        construction, bootstrap.py registers one built-in mock
        connector - "Mock External System" - backed by a
        MockConnector implementation, per Package 017's explicit "No
        real integrations yet. Use mock connectors only" requirement.
        Like AgentRuntime, and unlike Capability Registry, Plugin
        Manager, and Planner, ConnectorManager DOES implement
        IService, with invoke() genuinely gated on the manager's own
        RUNNING state - see argus/connectors/interfaces.py's
        Architectural Note and ADR-0002's newly appended Empirical
        Finding for that package. Like every other IService adopter,
        it is registered only (LifecycleState.REGISTERED) here - its
        own initialize()/start() are deliberately NOT called by this
        package, for the same divergence-avoidance reasoning recorded
        in ADR-0002 and already applied to every prior adopter.
    23. Construct the Cognitive Pipeline (depends on the Planner
        only) and register it with the Container, per Package 025.
        Bootstrap is the only place that constructs CognitivePipeline
        directly; every other subsystem must resolve it from the
        Container. Constructed immediately after the Connector
        Manager, per the Bootstrap section's explicit instruction
        ("Add it to bootstrap in the proper dependency order. Planner
        must already exist before Pipeline.") - like Memory
        Integration's, the Reasoning Engine's, and the Decision
        Engine's own placement, this ordering IS dependency-driven:
        CognitivePipeline genuinely needs a live IPlanner reference at
        construction, even though - unlike those three - it needs
        nothing else. This is the first new runtime service since
        Package 021 (Packages 022-023 deliberately introduced no new
        core service at all - see their own Architectural Notes).
        CognitivePipeline DOES implement IService, with run()
        genuinely gated on the pipeline's own RUNNING state - see
        argus/pipeline/interfaces.py's Architectural Note and
        ADR-0002's newly appended Empirical Finding for this package.
        Like every other IService adopter, it is registered only
        (LifecycleState.REGISTERED) here - its own initialize()/
        start() are deliberately NOT called by this package, for the
        same divergence-avoidance reasoning recorded in ADR-0002 and
        already applied to every prior adopter.
    24. Construct the Capability Executor (depends on the
        already-constructed CapabilityRegistry, genuinely called by
        every resolve() invocation; see
        argus.capability_executor.executor's own module docstring)
        and register it with the Container, per Package 034. Bootstrap
        is the only place that constructs CapabilityExecutor directly;
        every other subsystem must resolve it from the Container.
        Constructed immediately after the Cognitive Pipeline and
        immediately before the Execution Engine, per the Architectural
        Position diagram this package's own work order gives
        ("Execution Engine -> Capability Executor -> Capability
        Registry -> Capability") - this placement IS dependency-
        driven: CapabilityExecutor genuinely needs a live
        ICapabilityRegistry reference at construction, and the
        Execution Engine (step 25) in turn needs a live
        ICapabilityExecutor reference at its own construction. This is
        the fifth new runtime service since Package 021 (Packages
        022-023 deliberately introduced no new core service at all;
        Package 024 modified an existing one; Packages 029-031, and
        033, deliberately introduced no new core service either).
        CapabilityExecutor DOES implement IService, per the same
        "core service" reading already applied to the Response Engine
        (Package 027) and the Execution Engine (Package 032) - but
        resolve() is NOT gated on the executor's own RUNNING state,
        mirroring the Knowledge Graph (Package 018), the Reasoning
        Engine (Package 020), and the Decision Engine (Package 021) -
        each also zero-gated despite holding a genuine constructor
        dependency - see argus/capability_executor/interfaces.py's
        Architectural Note and ADR-0002's newly appended Empirical
        Finding for this package. Like every other IService adopter,
        it is registered only (LifecycleState.REGISTERED) here - its
        own initialize()/start() are deliberately NOT called by this
        package, for the same divergence-avoidance reasoning recorded
        in ADR-0002 and already applied to every prior adopter.
    25. Construct the Execution Engine (depends, as of Package 034,
        on the already-constructed CapabilityExecutor - genuinely
        called once per Task during execute(), replacing Package
        033's own stored-but-unused CapabilityRegistry reference; see
        argus.execution_engine.engine's own module docstring) and
        register it with the Container, per Package 032, amended by
        Packages 033 and 034. Bootstrap is the only place that
        constructs ExecutionEngine directly; every other subsystem
        must resolve it from the Container.
        Constructed immediately after the Capability Executor and
        immediately before the Response Engine, per the Bootstrap
        section's explicit dependency order ("Planner -> Pipeline ->
        Execution Engine -> Response Engine -> Agent") - it is placed
        here because the Agent Service (step 27) needs a live
        IExecutionEngine reference at its own construction, and the
        explicit dependency order names this position, while
        ExecutionEngine's own construction genuinely requires the
        already-constructed CapabilityExecutor (step 24). This is the
        fourth new runtime service since Package 021 (Packages 022-023
        deliberately introduced no new core service at all; Package
        024 modified an existing one; Packages 029-031 deliberately
        introduced no new core service either). ExecutionEngine DOES
        implement IService, per the same "core service" reading
        already applied to the Response Engine (Package 027) - but
        execute() is NOT gated on the engine's own RUNNING state,
        mirroring the Knowledge Graph (Package 018), the Reasoning
        Engine (Package 020), the Decision Engine (Package 021), the
        Response Engine (Package 027), and (as of this package) the
        Capability Executor - see
        argus/execution_engine/interfaces.py's Architectural Note and
        ADR-0002's newly appended Empirical Finding for this package.
        ResponseEngine (027) remains the sole core service in this
        codebase's own history with a fully empty constructor -
        ExecutionEngine held that distinction only briefly, from
        Package 032 until Package 033 gave it a (then-unused)
        constructor dependency; as of this package that dependency is
        both present and genuinely used. Like every other IService
        adopter, it is registered only (LifecycleState.REGISTERED)
        here - its own initialize()/start() are deliberately NOT
        called by this package, for the same divergence-avoidance
        reasoning recorded in ADR-0002 and already applied to every
        prior adopter.
    26. Construct the Response Engine (depends on nothing) and
        register it with the Container, per Package 027. Bootstrap is
        the only place that constructs ResponseEngine directly; every
        other subsystem must resolve it from the Container.
        Constructed immediately after the Execution Engine and
        immediately before the Agent Service, per the Bootstrap
        section's explicit dependency order ("Planner -> Pipeline ->
        Execution Engine -> Response Engine -> Agent") - unlike every
        other core service constructed so far except the Execution
        Engine immediately before it, this placement is dependency-
        driven in the weakest possible sense: nothing about
        ResponseEngine's own construction actually requires anything
        constructed before it ("ResponseEngine may depend only on:
        Plan," and Plan is a per-call argument to build_response(),
        never a constructor dependency) - it is placed here solely
        because the Agent Service (step 27) needs a live
        IResponseEngine reference at its own construction, and the
        explicit dependency order names this position. This is the
        third new runtime service since Package 021 (Packages 022-023
        deliberately introduced no new core service at all; Package
        024 modified an existing one). ResponseEngine DOES implement
        IService, per the same "core service" + "lifecycle" Testing
        category reading already applied to the Cognitive Pipeline
        (Package 025) and the Agent Service (Package 026) - but
        unlike either of those two, build_response() is NOT gated on
        the engine's own RUNNING state, mirroring the Knowledge Graph
        (Package 018), the Reasoning Engine (Package 020), and the
        Decision Engine (Package 021) - see
        argus/response/interfaces.py's Architectural Note and
        ADR-0002's newly appended Empirical Finding for this package.
        Like every other IService adopter, it is registered only
        (LifecycleState.REGISTERED) here - its own initialize()/
        start() are deliberately NOT called by this package, for the
        same divergence-avoidance reasoning recorded in ADR-0002 and
        already applied to every prior adopter.
    27. Construct the Agent Service (depends on the Cognitive
        Pipeline, the Execution Engine, and the Response Engine) and
        register it with the Container, per Packages 026, 027, and
        032. Bootstrap is the only place that constructs AgentService
        directly; every other subsystem must resolve it from the
        Container. Constructed immediately after the Response Engine,
        per the Bootstrap section's explicit dependency order
        ("Planner -> Pipeline -> Execution Engine -> Response Engine
        -> Agent") - like the Cognitive Pipeline's own placement
        (Package 025), this ordering IS dependency-driven: AgentService
        genuinely needs a live ICognitivePipeline reference, a live
        IExecutionEngine reference (as of this package), and a live
        IResponseEngine reference (as of Package 027) at construction,
        and nothing else - "AgentService may depend on:
        ICognitivePipeline. AgentService shall not depend on: Planner,
        Reasoning Engine, Decision Engine, Builders, Bootstrap
        internals" (Package 026), extended by Package 027's own
        "After pipeline.run() invoke response_engine.build_response()"
        instruction and this package's own "New flow: Pipeline ->
        Execution Engine -> Response Engine" instruction. AgentService
        DOES implement IService, with run() genuinely gated on the
        service's own RUNNING state - see argus/agent/interfaces.py's
        Architectural Note and ADR-0002's newly appended Empirical
        Finding for Package 026 (unaffected by this package's own
        amendment). Like every other IService adopter, it is
        registered only (LifecycleState.REGISTERED) here - its own
        initialize()/start() are deliberately NOT called by this
        package, for the same divergence-avoidance reasoning recorded
        in ADR-0002 and already applied to every prior adopter.
    28. Register the twenty-six core services (Configuration, Logger,
        Event Bus, Service Registry, Lifecycle Manager, Knowledge
        Service, Memory Service, Scheduler, Intent Router, Workflow
        Engine, Conversation Manager, Capability Registry, Intent
        Dispatcher, Plugin Manager, Planner, Knowledge Graph, Memory
        Integration, Reasoning Engine, Decision Engine, Agent Runtime,
        Connector Manager, Cognitive Pipeline, Capability Executor,
        Execution Engine, Response Engine, Agent Service) in the
        Service Registry (identity/descriptive data only) and in the
        Lifecycle Manager, where each enters LifecycleState.REGISTERED.
        None of them are
        initialized or started by this package.
    29. Construct and start the Application.

Scope:
    This module implements only application startup infrastructure.
    No engines (Atlas, Cortex, Hermes, Navigator, Sentinel) are
    initialized here. Packages 003-016 register the Event Bus, Service
    Registry, Lifecycle Manager, Knowledge Service, Memory Service,
    Scheduler, Intent Router, Workflow Engine, Conversation Manager,
    Capability Registry, Intent Dispatcher, Plugin Manager, Planner,
    and Agent Runtime respectively but do not change Application's
    lifecycle: no lifecycle events are published, and no core service
    is initialized or started, by this package (see the Package 005
    engineering notes).

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
from argus.connectors import Connector, ConnectorManager, IConnectorManager, MockConnector
from argus.container import Container
from argus.conversation import IConversationManager, ConversationManager
from argus.decision import DecisionEngine, IDecisionEngine
from argus.dispatcher import (
    DEFAULT_WORKFLOW_IDS,
    IIntentDispatcher,
    IntentDispatcher,
    WorkflowAction,
    build_action_from_capability,
)
from argus.events import IEventBus, InMemoryEventBus
from argus.capability_executor import CapabilityExecutor, ICapabilityExecutor
from argus.execution_engine import ExecutionEngine, IExecutionEngine
from argus.intent import IIntentRouter, IntentRouter
from argus.knowledge import IKnowledgeService, JSONKnowledgeStorage, KnowledgeService
from argus.knowledge_graph import IKnowledgeGraph, KnowledgeGraph
from argus.lifecycle import LifecycleManager
from argus.logging_service import get_logger, initialize_logging
from argus.memory import IMemoryService, JSONMemoryStorage, MemoryService
from argus.memory_integration import IMemoryIntegration, MemoryIntegration
from argus.agent import AgentService, IAgentService
from argus.response import IResponseEngine, ResponseEngine
from argus.pipeline import CognitivePipeline, ICognitivePipeline
from argus.planner import IPlanner, Planner
from argus.plugins import IPluginManager, Plugin, PluginManager
from argus.reasoning import IReasoningEngine, ReasoningEngine
from argus.runtime import AgentRuntime, IAgentRuntime
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
CORE_SERVICES_VERSION = "0.4.1"


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

    plugin_manager = PluginManager(event_bus=event_bus)
    plugin_manager.register(
        Plugin(
            name="Core Workflows",
            version="1.0.0",
            author="ArgusOS Core Team",
            description=(
                "Built-in plugin representing the five Version 1 "
                "workflow-backed capabilities registered directly by "
                "the Capability Registry population step above - the "
                "same Capability instances, not copies."
            ),
            exported_capabilities=tuple(capability_registry.list_capabilities()),
        )
    )
    container.register("plugin_manager", plugin_manager)

    intent_dispatcher = IntentDispatcher(
        event_bus=event_bus,
        capability_registry=capability_registry,
        action_factory=functools.partial(
            build_action_from_capability, workflow_engine=workflow_engine
        ),
    )
    container.register("intent_dispatcher", intent_dispatcher)

    planner = Planner(event_bus=event_bus, capability_registry=capability_registry)
    container.register("planner", planner)

    knowledge_graph = KnowledgeGraph(event_bus=event_bus)
    container.register("knowledge_graph", knowledge_graph)

    memory_integration = MemoryIntegration(
        memory_service=memory_service, knowledge_graph=knowledge_graph, event_bus=event_bus
    )
    container.register("memory_integration", memory_integration)

    reasoning_engine = ReasoningEngine(
        knowledge_graph=knowledge_graph,
        memory_integration=memory_integration,
        event_bus=event_bus,
    )
    container.register("reasoning_engine", reasoning_engine)

    decision_engine = DecisionEngine(reasoning_engine=reasoning_engine, event_bus=event_bus)
    container.register("decision_engine", decision_engine)

    agent_runtime = AgentRuntime(
        event_bus=event_bus, dispatcher=intent_dispatcher, planner=planner
    )
    container.register("agent_runtime", agent_runtime)

    connector_manager = ConnectorManager(event_bus=event_bus)
    connector_manager.register_connector(
        Connector(
            name="Mock External System",
            description=(
                "Built-in Version 1 connector demonstrating the "
                "Connector Framework end to end. Backed by a "
                "MockConnector implementation - per this package's "
                "'No real integrations yet. Use mock connectors only' "
                "requirement, it performs no network I/O of any kind."
            ),
            version="1.0.0",
            capabilities=("mock_operation",),
        ),
        MockConnector(),
    )
    container.register("connector_manager", connector_manager)

    cognitive_pipeline = CognitivePipeline(planner=planner)
    container.register("cognitive_pipeline", cognitive_pipeline)

    capability_executor = CapabilityExecutor(capability_registry=capability_registry)
    container.register("capability_executor", capability_executor)

    execution_engine = ExecutionEngine(capability_executor=capability_executor)
    container.register("execution_engine", execution_engine)

    response_engine = ResponseEngine()
    container.register("response_engine", response_engine)

    agent_service = AgentService(
        cognitive_pipeline=cognitive_pipeline,
        execution_engine=execution_engine,
        response_engine=response_engine,
    )
    container.register("agent_service", agent_service)

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
        plugin_manager=plugin_manager,
        planner=planner,
        knowledge_graph=knowledge_graph,
        memory_integration=memory_integration,
        reasoning_engine=reasoning_engine,
        decision_engine=decision_engine,
        agent_runtime=agent_runtime,
        connector_manager=connector_manager,
        cognitive_pipeline=cognitive_pipeline,
        capability_executor=capability_executor,
        execution_engine=execution_engine,
        response_engine=response_engine,
        agent_service=agent_service,
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
    plugin_manager: IPluginManager,
    planner: IPlanner,
    knowledge_graph: IKnowledgeGraph,
    memory_integration: IMemoryIntegration,
    reasoning_engine: IReasoningEngine,
    decision_engine: IDecisionEngine,
    agent_runtime: IAgentRuntime,
    connector_manager: IConnectorManager,
    cognitive_pipeline: ICognitivePipeline,
    capability_executor: ICapabilityExecutor,
    execution_engine: IExecutionEngine,
    response_engine: IResponseEngine,
    agent_service: IAgentService,
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
    Conversation Manager, the Capability Registry, the Intent
    Dispatcher, the Plugin Manager, the Planner, the Knowledge Graph,
    Memory Integration, the Reasoning Engine, the Decision Engine, the
    Agent Runtime, the Connector Manager, the Cognitive Pipeline, the
    Execution Engine, the Response Engine, and the Agent Service is
    recorded as a ServiceDescriptor (identity and descriptive data
    only, no runtime state) in the Service Registry, and as a
    LifecycleState.REGISTERED entry in the Lifecycle Manager, which is
    the sole owner of runtime lifecycle state for the Lifecycle
    Manager's own purposes. Neither initialize() nor start() is called
    on the Lifecycle Manager for any of them here. Scheduler, the
    Intent Router, the Workflow Engine, the Conversation Manager, the
    Intent Dispatcher, the Knowledge Graph, Memory Integration, the
    Reasoning Engine, the Decision Engine, the Agent Runtime, the
    Connector Manager, the Cognitive Pipeline, the Capability
    Executor, the Execution Engine, the Response Engine, and the Agent
    Service are sixteen of these twenty-six that actually implement
    IService (see ADR-0002) - though the Knowledge Graph, the
    Reasoning Engine, the Decision Engine, the Response Engine, the
    Execution Engine, and the Capability Executor, each per its own
    explicit work order instruction rather than an independent
    application of ADR-0002's criterion, are the second through
    seventh of these sixteen (after the Intent Router) with no method
    gated on the RUNNING state at all - the Response Engine remains
    the sole one of these seven for which the underlying reason is
    "the service holds no constructor dependency whatsoever"
    ("ResponseEngine may depend only on: Plan," a per-call argument,
    never injected); the Knowledge Graph, the Reasoning Engine, the
    Decision Engine, the Execution Engine (as of Package 034, via its
    own CapabilityExecutor dependency), and the Capability Executor
    itself are each zero-gated despite holding a genuine constructor
    dependency, since none of their own methods perform an effectful,
    stateful, or external operation a RUNNING/not-RUNNING distinction
    could meaningfully police (see each one's own interfaces.py
    Architectural Note for the full reasoning); Memory Integration,
    the Cognitive Pipeline, and the Agent Service, by contrast, are
    each explicitly instructed to adopt IService AND independently
    satisfy ADR-0002's criterion on its own merits
    (synchronize_memory()/synchronize_all()/remove_memory(), run(),
    and run(), respectively, are genuinely gated) - see ADR-0002's
    newly appended Empirical Findings for Packages 019, 020, 021, 025,
    026, 027, 032, and 034. The Capability Registry, the Plugin
    Manager, and the Planner deliberately do not implement IService at
    all (see argus/capability/interfaces.py's,
    argus/plugins/interfaces.py's, and argus/planner/interfaces.py's
    Architectural Notes). This function still does not call any
    IService adopter's initialize()/start() directly - see the
    Startup Sequence note in this module's docstring for why
    exercising their real IService lifecycles during bootstrap was
    deliberately avoided.

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
        plugin_manager: The Plugin Manager instance.
        planner: The Planner instance.
        knowledge_graph: The Knowledge Graph instance.
        memory_integration: The Memory Integration instance.
        reasoning_engine: The Reasoning Engine instance.
        decision_engine: The Decision Engine instance.
        agent_runtime: The Agent Runtime instance.
        connector_manager: The Connector Manager instance.
        cognitive_pipeline: The Cognitive Pipeline instance.
        capability_executor: The Capability Executor instance.
        execution_engine: The Execution Engine instance.
        response_engine: The Response Engine instance.
        agent_service: The Agent Service instance.
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
        ("plugin_manager", plugin_manager, IPluginManager),
        ("planner", planner, IPlanner),
        ("knowledge_graph", knowledge_graph, IKnowledgeGraph),
        ("memory_integration", memory_integration, IMemoryIntegration),
        ("reasoning_engine", reasoning_engine, IReasoningEngine),
        ("decision_engine", decision_engine, IDecisionEngine),
        ("agent_runtime", agent_runtime, IAgentRuntime),
        ("connector_manager", connector_manager, IConnectorManager),
        ("cognitive_pipeline", cognitive_pipeline, ICognitivePipeline),
        ("capability_executor", capability_executor, ICapabilityExecutor),
        ("execution_engine", execution_engine, IExecutionEngine),
        ("response_engine", response_engine, IResponseEngine),
        ("agent_service", agent_service, IAgentService),
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
