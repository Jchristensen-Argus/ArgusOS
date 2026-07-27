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