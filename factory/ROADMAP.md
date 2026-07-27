# Argus Factory Roadmap

## Phase 1 — Foundation
- [x] Architecture
- [x] Specifications
- [x] Coding Standards
- [x] ADR Process
- [x] Implementation Packages
- [x] Bootstrap
- [ ] Configuration (minimal loader shipped with Bootstrap; full CONFIGURATION.md service still pending)
- [ ] Logging (minimal service shipped with Bootstrap; full LOGGING.md service still pending)
- [x] Event Bus
- [x] Service Registry
- [x] Dependency Injection
- [x] Lifecycle (Application start/shutdown, Package 002)
- [x] Service Lifecycle Framework (IService, LifecycleManager, Package 005)
- [x] Knowledge Service (KnowledgeRecord, IKnowledgeStorage/IKnowledgeService, JSONKnowledgeStorage, KnowledgeService, Package 006)
- [x] Memory Service (MemoryRecord, IMemoryStorage/IMemoryService, JSONMemoryStorage, MemoryService, Package 007)
- [x] Scheduler Service (ScheduledTask, Trigger/OneShotTrigger/IntervalTrigger/DailyTrigger, IScheduler(IService), Scheduler, Package 008)
- [x] Intent Router (Intent/IntentType, parse_text, IIntentRouter(IService), IntentRouter, Package 009)
- [x] Workflow Engine (Workflow/WorkflowStep, WorkflowState, IWorkflowEngine(IService), WorkflowEngine, Package 010)
- [x] Conversation Manager (ConversationSession/ConversationMessage, ConversationState, IConversationManager(IService), ConversationManager, Package 011)
- [x] Intent Dispatcher (Action/WorkflowAction, IIntentDispatcher(IService), IntentDispatcher, Package 012; revised in Package 013 to resolve Capabilities instead of holding its own mapping)
- [x] Capability Registry (Capability, ICapabilityRegistry, CapabilityRegistry, Package 013)
- [x] Plugin Manager (Plugin, IPluginManager, PluginManager, Package 014)
- [x] Planner (Plan, PlanStep, PlanStatus, IPlanner, Planner, Package 015)
- [x] Agent Runtime (Execution, ExecutionStatus, IAgentRuntime, AgentRuntime, Package 016)
- [x] Connector Framework (Connector, IConnector, IConnectorManager, ConnectorManager, MockConnector, Package 017)
- [x] Knowledge Graph (Entity, Relationship, IKnowledgeGraph, KnowledgeGraph, Package 018)
- [x] Memory Integration (MemoryMapper, IMemoryIntegration, MemoryIntegration, Package 019)
- [x] Reasoning Engine (ReasoningQuery, ReasoningResult, IReasoningEngine, ReasoningEngine, Package 020)
- [x] Decision Engine (DecisionRule, Decision, IDecisionEngine, DecisionEngine, Package 021)
- [x] Cognitive Context (CognitiveContext, ContextMetadata, ICognitiveContextBuilder, ContextBuilder, Package 022 - transport object only; no new core service, no new events, no bootstrap changes)
- [x] Planning Session (PlanningSession, PlanningGoal, PlanningConstraint, PlanningMetadata, IPlanningSessionBuilder, PlanningSessionBuilder, Package 023 - transport object only; no new core service, no new events, no bootstrap changes)
- [x] Planner Session Integration (Planner.plan_session(), Package 024 - additive PlanningSession entry point delegating to create_plan()/add_step(); no new core service, no new events, no bootstrap changes, full backward compatibility)
- [x] Cognitive Pipeline (CognitivePipeline, ICognitivePipeline, PipelineRequest, PipelineResult, Package 025 - first-generation orchestrator wiring Conversation -> Cognitive Context -> Planning Session -> Planner.plan_session(); twenty-second core service, twelfth IService adopter, no new events, no reasoning/planning behavior change)
- [x] Agent Session (AgentSession, AgentRequest, AgentResponse, IAgentService, AgentService, Package 026 - first-generation user-facing orchestration layer wiring User -> Agent Session -> Cognitive Pipeline; twenty-third core service, thirteenth IService adopter, no new events, wraps PipelineResult only - no natural language, no execution)
- [x] Response Engine (Response, ResponseMetadata, IResponseEngine, ResponseEngine, Package 027 - first-generation transformation layer converting a validated Plan into a standardized Response; twenty-fourth core service, fourteenth IService adopter (fifth zero-gated, first with no constructor dependency at all), no new events, no AI/formatting/rendering; AgentResponse amended to wrap Response instead of PipelineResult)
- [x] Execution Trace (ExecutionTrace, TraceStep, TraceMetadata, ITraceBuilder, TraceBuilder, Package 028 - first-generation immutable record of how a request moved through Argus, built inside AgentService and embedded in Response.execution_trace; no new core service, no new events, no bootstrap changes - "TraceBuilder is not a service")
- [x] Task Model (Task, TaskStatus, TaskMetadata, ITaskBuilder, TaskBuilder, Package 029 - first-generation immutable description of a single unit of work produced by a Plan; no execution, no new core service, no new events, no bootstrap changes, fully isolated - does not modify Planner/Plan/Pipeline/Response/Agent/Execution Trace)
- [x] Plan Task Integration (Plan.tasks, PlanningSession.tasks, PlanningSessionBuilder.with_task()/with_tasks()/clear_tasks(), Planner.create_plan(tasks=...)/plan_session() carry-through, Package 030 - a Plan (and PlanningSession) now owns an ordered, immutable collection of Tasks; no execution, no new core service, no new events, no bootstrap changes - "The Planner owns Tasks, but does not perform them")
- [x] Task Relationships (TaskRelationship, RelationshipType, RelationshipMetadata, IRelationshipBuilder, RelationshipBuilder, Task.relationships, TaskBuilder.with_relationship()/with_relationships()/clear_relationships(), Package 031 - a Task now owns an ordered, immutable collection of purely descriptive TaskRelationships to other Tasks; no scheduling, no dependency resolution, no new core service, no new events, no bootstrap changes - "Relationships describe work - they do not coordinate it")
- [x] Execution Engine (ExecutionResult, ExecutionStatus, ExecutionMetadata, IExecutionResultBuilder, ExecutionResultBuilder, IExecutionEngine, ExecutionEngine, Package 032 - first-generation lifecycle-only execution stage inserted between Cognitive Pipeline and Response Engine; twenty-fifth core service, fifteenth IService adopter (sixth zero-gated, second with no constructor dependency at all); every Task considered successfully processed, no tool invocation/API calls/AI, no new events - "It simply establishes the execution lifecycle")
- [x] Capability Framework (CapabilityMetadata, CapabilityBuilder, ICapabilityBuilder, Package 033 - extends the existing Package 013 argus/capability/ package in place, adding version/capability_metadata fields to Capability, a dedicated CapabilityBuilder, and CapabilityRegistry.get_by_name()/duplicate-name rejection; new architecture Planner -> Plan -> Execution Engine -> Capability Registry -> Capability; ExecutionEngine constructor now accepts a CapabilityRegistry reference, stored but never called; no new core service, no new events, no dispatch model yet - "The framework simply establishes the contracts and registration mechanism")
- [x] Capability Executor (CapabilityExecutionResult, CapabilityExecutionStatus, CapabilityExecutionMetadata, CapabilityExecutionResultBuilder, ICapabilityExecutionResultBuilder, CapabilityExecutor, ICapabilityExecutor, Package 034 - first-generation deterministic Task-to-Capability dispatch by exact name match; new architecture Execution Engine -> Capability Executor -> Capability Registry -> Capability; ExecutionEngine constructor now accepts a CapabilityExecutor, replacing its own Package 033 CapabilityRegistry reference, genuinely called once per Task; twenty-sixth core service, sixteenth IService adopter (seventh zero-gated); no Capability invocation, no execution policy, ExecutionEngine still ignores the returned status - "It establishes the execution contract only")
- [x] Capability Context (CapabilityContext, CapabilityContextMetadata, CapabilityContextBuilder, ICapabilityContextBuilder, Package 035 - immutable snapshot of everything a Capability will eventually need (Task, Plan, ExecutionTrace, metadata), created once per Task and passed through the execution pipeline; new architecture Execution Engine -> Capability Context -> Capability Executor; CapabilityExecutor.resolve() now accepts a CapabilityContext, replacing its own Package 034 bare-Task parameter, resolution behavior unchanged; no new core service, bootstrap.py unmodified (no builder has ever been registered as a service); execution_trace always None in Version 1 since no genuine ExecutionTrace exists at context-construction time - "The context is simply created and passed through the execution pipeline")
- [x] Project Framework (Project, ProjectStatus, ProjectMetadata, ProjectBuilder, IProjectBuilder, Package 036 - the top-level organizational unit for long-running work (examples: Just Tallow, Packaging Sales, ArgusOS, Book Publishing, Real Estate, Marketing, Personal); new architecture Project -> Goal -> Plan -> Task, with Goal not yet implemented; standalone value object with a dedicated builder, no service, no integration, no bootstrap changes - the first package to modify zero pre-existing files; ProjectMetadata gains owner/tags alongside the established created_at/version/correlation_id/extra quartet, neither settable via ProjectBuilder in Version 1; future ownership of Goals/Documents/Knowledge/Conversations/Assets/Campaigns documented only, not implemented - "Project is a passive domain object only")
- [x] Workspace Framework (Workspace, WorkspaceStatus, WorkspaceMetadata, WorkspaceBuilder, IWorkspaceBuilder, Package 037 - the highest-level organizational boundary within Argus (examples: Joel Christensen, Deline Box & Display, Just Tallow, Family, Sandbox); new architecture Workspace -> Project -> Goal -> Plan -> Task, with Goal still not implemented; standalone value object with a dedicated builder, no service, no integration, no bootstrap changes - the second consecutive package to modify zero pre-existing files; WorkspaceMetadata follows ProjectMetadata's own exact created_at/version/correlation_id/owner/tags/extra field order, neither owner nor tags settable via WorkspaceBuilder in Version 1; WorkspaceStatus defaults to ACTIVE (not a "not yet begun" state, unlike ProjectStatus.PLANNING); future ownership of Projects/Users/Shared Knowledge/Shared Assets/Automations/Credentials/Configuration/Policies/Models/Memory documented only, not implemented - "Workspace is a passive domain object only")
- [x] Goal Framework (Goal, GoalStatus, GoalPriority, GoalMetadata, GoalBuilder, IGoalBuilder, Package 038 - a desired outcome within a Project (examples: Grow Just Tallow revenue 20%, Publish the ArgusOS architecture book, Launch the Q3 marketing campaign); new architecture Workspace -> Project -> Goal -> Plan -> Task, now fully populated with domain objects at every link; standalone value object with a dedicated builder, no service, no integration, no bootstrap changes - the third consecutive package to modify zero pre-existing files; GoalMetadata follows ProjectMetadata's and WorkspaceMetadata's own exact created_at/version/correlation_id/owner/tags/extra field order, neither owner nor tags settable via GoalBuilder in Version 1; GoalPriority is a plain Enum with no ordering behavior, defaulting to NORMAL rather than LOW - the first deliberate exception to this codebase's own "first-listed member is the default" convention; GoalStatus defaults to PLANNING and ends in ABANDONED rather than ARCHIVED; future ownership of Plans/Success metrics/Milestones/Decisions/Deadlines/Risks/Dependencies documented only, not implemented - "Goals are passive domain objects only")

---

## Phase 2 — Core Engines

- [x] Memory (short-term, expiry-aware working memory shipped as a Foundation-phase core service, Package 007; see Phase 1 above)
- [x] Scheduler (tick()-driven, background-thread-free scheduling shipped as a Foundation-phase core service, Package 008; see Phase 1 above — this is not the full Navigator-integrated engine design/specifications/SCHEDULER.md describes, since Navigator does not exist yet, see factory/packages/008_SCHEDULER_SERVICE.md's Scope Reduction)
- [ ] Atlas (blocked on: none currently — Memory Service, its one Required Dependency, now exists)
- [ ] Cortex (blocked on: no specification file exists yet in design/specifications/)
- [ ] Hermes (blocked on: Cortex)
- [ ] Navigator (blocked on: Cortex, Hermes; Scheduler's core-service form now exists, see Phase 1)
- [ ] Sentinel (no blockers — Event Bus, Logging, Configuration all exist; not yet selected as a package, see factory/packages/007_MEMORY_SERVICE.md)

---

## Phase 3 — Applications

- [ ] Packaging
- [ ] Trading
- [ ] Realty
- [ ] Tallow

---

## Phase 4 — Intelligence

- [ ] Multi-agent coordination
- [ ] Long-term memory
- [ ] Autonomous planning
- [ ] Continuous learning