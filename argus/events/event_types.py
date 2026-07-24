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
