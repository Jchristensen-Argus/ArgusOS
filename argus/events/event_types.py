"""
Event type and priority enumerations for the ArgusOS Event Bus.

Purpose:
    Define the closed set of event categories and priority levels that
    can be attached to an Event, per
    factory/packages/003_EVENT_BUS.md.

Scope:
    EventType is intentionally minimal for this package. Future
    packages will extend the list of values as new subsystems come
    online; this module is the single place new event types are added.

Dependencies:
    None (standard library only).
"""

from enum import Enum, auto


class EventPriority(Enum):
    """Relative priority of an event. Informational only in this
    package: the Event Bus does not use priority for scheduling or
    delivery order (see Package 003 Non-Goals)."""

    LOW = auto()
    NORMAL = auto()
    HIGH = auto()
    CRITICAL = auto()


class EventType(Enum):
    """The closed set of event types ArgusOS subsystems may publish."""

    SYSTEM_STARTED = "system_started"
    SYSTEM_STOPPING = "system_stopping"
    SYSTEM_STOPPED = "system_stopped"
    SERVICE_STARTED = "service_started"
    SERVICE_STOPPED = "service_stopped"
    EVENT_PUBLISHED = "event_published"
    USER_COMMAND = "user_command"
    MEMORY_UPDATED = "memory_updated"
    SCHEDULER_TICK = "scheduler_tick"
    LOG_MESSAGE = "log_message"

    # Added by Package 006 - Knowledge Service, per this module's own
    # "single place new event types are added" scope note above.
    # KnowledgeService publishes these on the existing Event Bus after
    # each successful put / update / delete (see
    # argus/knowledge/knowledge_service.py).
    KNOWLEDGE_CREATED = "knowledge_created"
    KNOWLEDGE_UPDATED = "knowledge_updated"
    KNOWLEDGE_DELETED = "knowledge_deleted"

    # Added by Package 008 - Scheduler Service, per this module's own
    # "single place new event types are added" scope note above.
    # Scheduler publishes these on the existing Event Bus for every
    # task lifecycle transition (see
    # argus/scheduler/scheduler.py). SCHEDULER_TICK, reserved since
    # Package 003 and unused until now, is published once per tick()
    # call as a heartbeat, separate from the per-task events below.
    TASK_SCHEDULED = "task_scheduled"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_CANCELLED = "task_cancelled"
    TASK_PAUSED = "task_paused"
    TASK_RESUMED = "task_resumed"

    # Added by Package 009 - Intent Router, per this module's own
    # "single place new event types are added" scope note above.
    # IntentRouter publishes these on the existing Event Bus (see
    # argus/intent/router.py). INTENT_PARSED fires for every parse()
    # call, including UNKNOWN results (there is no such thing as
    # invalid string input to the parser - only unrecognized-but-
    # valid string input). INTENT_ROUTED fires for every route() call
    # and is what register_handler()'s Event-Bus subscriptions filter
    # from. INTENT_FAILED fires for router-level failures (invalid
    # non-string input to parse(), invalid non-Intent input to
    # route()) and, separately, for isolated per-handler failures
    # caught during register_handler()'s dispatch.
    INTENT_PARSED = "intent_parsed"
    INTENT_ROUTED = "intent_routed"
    INTENT_FAILED = "intent_failed"

    # Added by Package 010 - Workflow Engine, per this module's own
    # "single place new event types are added" scope note above.
    # WorkflowEngine publishes these on the existing Event Bus (see
    # argus/workflow/engine.py). WORKFLOW_STARTED fires once per
    # execute() call, before the first step runs. WORKFLOW_STEP_STARTED
    # and WORKFLOW_STEP_COMPLETED bracket each individual step in
    # order. WORKFLOW_COMPLETED fires once all steps succeed;
    # WORKFLOW_FAILED fires instead if a step raises, and execution
    # stops - no further steps run and no WORKFLOW_COMPLETED follows.
    # WORKFLOW_CANCELLED fires only from cancel(), never from
    # execute() - a workflow may only be cancelled while PENDING.
    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_STEP_STARTED = "workflow_step_started"
    WORKFLOW_STEP_COMPLETED = "workflow_step_completed"
    WORKFLOW_COMPLETED = "workflow_completed"
    WORKFLOW_FAILED = "workflow_failed"
    WORKFLOW_CANCELLED = "workflow_cancelled"

    # Added by Package 011 - Conversation Manager, per this module's
    # own "single place new event types are added" scope note above.
    # ConversationManager publishes these on the existing Event Bus
    # (see argus/conversation/manager.py). CONVERSATION_STARTED and
    # CONVERSATION_ENDED bracket a session's lifetime.
    # MESSAGE_RECEIVED fires once per receive() call, right after the
    # user's message is appended to history. INTENT_RESOLVED fires
    # after IIntentRouter.parse() returns (delegated classification,
    # not performed by ConversationManager itself). WORKFLOW_EXECUTED
    # fires only when receive() was given a workflow_id that the
    # Workflow Engine successfully executed (delegated execution, not
    # performed by ConversationManager itself) - it does not fire if
    # no workflow_id was supplied or the delegated execute() call
    # failed. RESPONSE_GENERATED fires once per receive() call, right
    # after the assistant's reply is appended to history.
    CONVERSATION_STARTED = "conversation_started"
    MESSAGE_RECEIVED = "message_received"
    INTENT_RESOLVED = "intent_resolved"
    WORKFLOW_EXECUTED = "workflow_executed"
    RESPONSE_GENERATED = "response_generated"
    CONVERSATION_ENDED = "conversation_ended"

    # Added by Package 012 - Intent Dispatcher, per this module's own
    # "single place new event types are added" scope note above.
    # IntentDispatcher publishes these on the existing Event Bus (see
    # argus/dispatcher/dispatcher.py). INTENT_DISPATCHED fires once
    # per dispatch() call, right after the lifecycle-state gate and
    # input validation pass - marking that an Intent has entered the
    # dispatch pipeline. ACTION_RESOLVED fires after resolve()
    # successfully finds the Intent's mapped Action. WORKFLOW_SELECTED
    # fires only when the resolved Action is specifically a
    # WorkflowAction, carrying its workflow_id - it does not fire for
    # any other Action kind. DISPATCH_STARTED fires immediately before
    # the resolved Action's execute() is called. DISPATCH_COMPLETED
    # fires once execute() returns successfully; DISPATCH_FAILED fires
    # instead - with a "stage" payload field of "resolve" or "execute"
    # - if resolve() finds no mapping or the resolved Action's
    # execute() raises. DISPATCH_FAILED and DISPATCH_COMPLETED are
    # mutually exclusive outcomes for a single dispatch() call, the
    # same way WORKFLOW_FAILED/WORKFLOW_COMPLETED are for execute()
    # (Package 010).
    INTENT_DISPATCHED = "intent_dispatched"
    ACTION_RESOLVED = "action_resolved"
    WORKFLOW_SELECTED = "workflow_selected"
    DISPATCH_STARTED = "dispatch_started"
    DISPATCH_COMPLETED = "dispatch_completed"
    DISPATCH_FAILED = "dispatch_failed"

    # Added by Package 013 - Capability Registry, per this module's
    # own "single place new event types are added" scope note above.
    # CapabilityRegistry publishes these on the existing Event Bus
    # (see argus/capability/registry.py), mirroring KnowledgeService's
    # KNOWLEDGE_CREATED/KNOWLEDGE_DELETED precedent (Package 006) for a
    # metadata CRUD store. CAPABILITY_REGISTERED fires once per
    # successful register() call; CAPABILITY_UNREGISTERED fires once
    # per successful unregister() call. Neither fires for a failed
    # (validation error, duplicate, or not-found) call.
    CAPABILITY_REGISTERED = "capability_registered"
    CAPABILITY_UNREGISTERED = "capability_unregistered"

    # Added by Package 014 - Plugin Manager, per this module's own
    # "single place new event types are added" scope note above.
    # PluginManager publishes these on the existing Event Bus (see
    # argus/plugins/manager.py), mirroring CapabilityRegistry's
    # CAPABILITY_REGISTERED/CAPABILITY_UNREGISTERED precedent (Package
    # 013) for a metadata CRUD store, extended with two more events
    # for this package's two additional lifecycle operations.
    # PLUGIN_REGISTERED fires once per successful register() call;
    # PLUGIN_UNREGISTERED fires once per successful unregister() call.
    # PLUGIN_ENABLED fires once per successful enable() call (even if
    # the plugin was already enabled); PLUGIN_DISABLED fires once per
    # successful disable() call (even if the plugin was already
    # disabled). None of the four fire for a failed (validation
    # error, duplicate, or not-found) call.
    PLUGIN_REGISTERED = "plugin_registered"
    PLUGIN_UNREGISTERED = "plugin_unregistered"
    PLUGIN_ENABLED = "plugin_enabled"
    PLUGIN_DISABLED = "plugin_disabled"

    # Added by Package 015 - Planner, per this module's own "single
    # place new event types are added" scope note above. Planner
    # publishes these on the existing Event Bus (see
    # argus/planner/planner.py). PLAN_CREATED fires once per
    # successful create_plan() call. PLAN_UPDATED fires once per
    # successful add_step()/remove_step()/reorder_steps() call - its
    # payload's "change" field distinguishes which
    # ("added_step"/"removed_step"/"reordered"), rather than three
    # separate event types for what is, from any subscriber's
    # perspective, the same underlying signal: "this Plan's steps
    # changed." PLAN_VALIDATED fires only when validate_plan()
    # succeeds (every non-optional step's required_capability is
    # registered) - a failed validate_plan() call raises
    # PlanValidationError instead and publishes nothing, matching
    # CapabilityRegistry.register()'s and PluginManager.register()'s
    # identical "failure raises, does not publish" precedent. No
    # PLAN_REMOVED event exists: this package has no "delete an
    # entire Plan" operation for it to correspond to - only
    # step-level removal, already covered by PLAN_UPDATED.
    PLAN_CREATED = "plan_created"
    PLAN_UPDATED = "plan_updated"
    PLAN_VALIDATED = "plan_validated"

    # Added by Package 016 - Agent Runtime, per this module's own
    # "single place new event types are added" scope note above.
    # AgentRuntime publishes these on the existing Event Bus (see
    # argus/runtime/runtime.py). EXECUTION_CREATED fires once per
    # start_execution() call, before any step is dispatched.
    # EXECUTION_STARTED fires immediately after, once the Execution's
    # status becomes RUNNING. STEP_STARTED/STEP_COMPLETED bracket each
    # individual PlanStep's Dispatcher.dispatch() call, in order.
    # EXECUTION_COMPLETED fires once every step has been dispatched
    # successfully; EXECUTION_FAILED fires instead - and execution
    # stops immediately, no further steps run - if a step's dispatch()
    # call raises. EXECUTION_FAILED and EXECUTION_COMPLETED are
    # mutually exclusive outcomes for a single run, the same way
    # WORKFLOW_FAILED/WORKFLOW_COMPLETED are for WorkflowEngine.execute()
    # (Package 010) and DISPATCH_FAILED/DISPATCH_COMPLETED are for
    # IntentDispatcher.dispatch() (Package 012). No dedicated event
    # exists for pause_execution()/resume_execution()/cancel_execution()
    # - this package's own Events section names exactly these six event
    # types; see factory/packages/016_AGENT_RUNTIME.md's Architectural
    # Decisions for why none were added to fill that gap.
    EXECUTION_CREATED = "execution_created"
    EXECUTION_STARTED = "execution_started"
    STEP_STARTED = "step_started"
    STEP_COMPLETED = "step_completed"
    EXECUTION_COMPLETED = "execution_completed"
    EXECUTION_FAILED = "execution_failed"

    # Added by Package 017 - Connector Framework, per this module's
    # own "single place new event types are added" scope note above.
    # ConnectorManager publishes these on the existing Event Bus (see
    # argus/connectors/manager.py). CONNECTOR_REGISTERED fires once
    # per successful register_connector() call. CONNECTOR_ENABLED
    # fires once per successful enable_connector() call (even if the
    # connector was already enabled); CONNECTOR_DISABLED fires once
    # per successful disable_connector() call (even if the connector
    # was already disabled) - mirroring PLUGIN_ENABLED/PLUGIN_DISABLED's
    # identical "fires regardless of prior state" precedent.
    # CONNECTOR_INVOKED fires once per successful invoke() call, after
    # the underlying connector implementation's connect() and invoke()
    # calls both return without raising. CONNECTOR_FAILED fires
    # instead - and the underlying error is re-raised, wrapped, to the
    # caller - if either call raises, mirroring
    # EXECUTION_FAILED/STEP_EXECUTION_ERROR's "publish then raise"
    # precedent (Package 016). No dedicated event exists for
    # unregister_connector(): this package's own Events section names
    # exactly these five event types; matching PLAN_REMOVED's
    # (Package 015) and pause/resume/cancel's (Package 016) precedent
    # of not inventing an event beyond what was explicitly asked for.
    CONNECTOR_REGISTERED = "connector_registered"
    CONNECTOR_ENABLED = "connector_enabled"
    CONNECTOR_DISABLED = "connector_disabled"
    CONNECTOR_INVOKED = "connector_invoked"
    CONNECTOR_FAILED = "connector_failed"

    # Added by Package 018 - Knowledge Graph, per this module's own
    # "single place new event types are added" scope note above.
    # KnowledgeGraph publishes these on the existing Event Bus (see
    # argus/knowledge_graph/graph.py). ENTITY_ADDED fires once per
    # successful add_entity() call. ENTITY_REMOVED fires once per
    # successful remove_entity() call - including when that call also
    # cascades to remove Relationships referencing the removed Entity
    # (see graph.py's own Cascading Removal note); cascaded
    # Relationship removals do not each publish their own
    # RELATIONSHIP_REMOVED, only the single ENTITY_REMOVED for the
    # call that triggered them, mirroring
    # ConnectorManager.unregister_connector()'s (Package 017) "one
    # call, one event" precedent. RELATIONSHIP_ADDED fires once per
    # successful add_relationship() call. RELATIONSHIP_REMOVED fires
    # once per successful, direct remove_relationship() call only.
    # None of the four fire for a failed (validation error, duplicate,
    # not-found, or invalid-reference) call.
    ENTITY_ADDED = "entity_added"
    ENTITY_REMOVED = "entity_removed"
    RELATIONSHIP_ADDED = "relationship_added"
    RELATIONSHIP_REMOVED = "relationship_removed"

    # Added by Package 019 - Memory Integration, per this module's own
    # "single place new event types are added" scope note above.
    # MemoryIntegration publishes these on the existing Event Bus (see
    # argus/memory_integration/integration.py). MEMORY_SYNCHRONIZED
    # fires once per successful synchronize_memory() call, after the
    # corresponding graph Entity has been added or reconciled -
    # regardless of whether any of that record's `related_keys`
    # Relationships also succeeded. MEMORY_DESYNCHRONIZED fires once
    # per successful remove_memory() call. MEMORY_MAPPING_FAILED fires
    # for any translation or graph-application failure -
    # Entity-level failures (synchronize_memory() also raises
    # MemoryMappingError in that case) as well as individual
    # Relationship-level failures, which are best-effort and do not
    # raise or abort the surrounding synchronize_memory() call. None
    # of the three fire for a failure that occurs before any Memory
    # Service or Knowledge Graph call is attempted (for example, an
    # unknown key, which raises InvalidMemoryRecordError directly).
    MEMORY_SYNCHRONIZED = "memory_synchronized"
    MEMORY_DESYNCHRONIZED = "memory_desynchronized"
    MEMORY_MAPPING_FAILED = "memory_mapping_failed"

    # Added by Package 020 - Reasoning Engine, per this module's own
    # "single place new event types are added" scope note above.
    # ReasoningEngine publishes these on the existing Event Bus (see
    # argus/reasoning/engine.py). Every one of the six public methods
    # (query/neighbors/find_paths/related_entities/entity_summary/
    # relationship_summary) publishes exactly one of two mutually
    # exclusive outcomes per call: on success,
    # REASONING_QUERY_EXECUTED fires first - marking that the
    # underlying read-only Knowledge Graph (and, for metadata only,
    # Memory Integration) calls completed - immediately followed by
    # REASONING_RESULT_CREATED, marking that a structured
    # ReasoningResult was subsequently assembled from them; on
    # failure (a malformed query/parameters, or an entity_id/
    # source_entity_id/target_entity_id with no corresponding
    # registered Entity), REASONING_QUERY_FAILED fires alone instead,
    # and neither of the other two fires - mirroring
    # CONNECTOR_INVOKED/CONNECTOR_FAILED's (Package 017) "mutually
    # exclusive outcomes for a single call" precedent, extended here
    # to three events only because this package's own Events section
    # names three, not two.
    REASONING_QUERY_EXECUTED = "reasoning_query_executed"
    REASONING_RESULT_CREATED = "reasoning_result_created"
    REASONING_QUERY_FAILED = "reasoning_query_failed"

    # Added by Package 021 - Decision Engine, per this module's own
    # "single place new event types are added" scope note above.
    # DecisionEngine publishes these on the existing Event Bus (see
    # argus/decision/engine.py). Every evaluate()/evaluate_all() call
    # publishes exactly one of two mutually exclusive outcomes: on
    # success, DECISION_EVALUATED fires first - marking that every
    # registered DecisionRule's predicate has been run against the
    # given ReasoningResult(s) - immediately followed by
    # DECISION_CREATED, marking that a structured Decision was
    # subsequently assembled from the results; on failure (malformed
    # input, or a registered rule's own predicate raising),
    # DECISION_FAILED fires alone instead, and neither of the other
    # two fires - mirroring REASONING_QUERY_EXECUTED/
    # REASONING_RESULT_CREATED/REASONING_QUERY_FAILED's (Package 020)
    # identical three-event, two-outcome shape. No event exists for
    # register_rule()/remove_rule(): this package's own Events section
    # names exactly these three event types, all evaluation-lifecycle
    # - matching PLAN_REMOVED's (Package 015) and Connector Manager's
    # unregister_connector()'s (Package 017) precedent of not inventing
    # an event beyond what was explicitly asked for.
    DECISION_EVALUATED = "decision_evaluated"
    DECISION_CREATED = "decision_created"
    DECISION_FAILED = "decision_failed"
