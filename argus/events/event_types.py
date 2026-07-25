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
