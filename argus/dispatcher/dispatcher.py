"""
IntentDispatcher: deterministic mapping-and-delegation for the ArgusOS
Intent Dispatcher.

Purpose:
    Implement IIntentDispatcher: translate a resolved Intent into an
    executable Action via a configurable mapping table, and delegate
    execution to that Action - never to IWorkflowEngine or any other
    backend directly - per
    factory/packages/012_INTENT_DISPATCHER.md.

Responsibilities:
    - register_mapping / remove_mapping / resolve / list_mappings: an
      in-memory registry of Action objects, keyed by IntentType.
      Registry operations are not affected by the dispatcher's own
      IService lifecycle state, matching the precedent set by
      Scheduler's schedule/cancel/pause/resume (Package 008),
      WorkflowEngine's register_workflow/cancel/get_workflow (Package
      010), and ConversationManager's start_session/end_session/
      history/active_session (Package 011).
    - dispatch: resolve an Intent to its registered Action and call
      that Action's own execute() method - the dispatcher never
      inspects, constructs, or reasons about what the Action actually
      does beyond calling execute() on it and, for WorkflowAction
      specifically, reading its workflow_id to publish
      WorkflowSelected (see the module's Non-Responsibilities for why
      this one exception exists). Publishes IntentDispatched,
      ActionResolved, WorkflowSelected (WorkflowAction only),
      DispatchStarted, and then DispatchCompleted or DispatchFailed,
      per IIntentDispatcher.dispatch()'s docstring.
    - initialize / start / stop / status, per the inherited IService
      contract. dispatch() *is* gated on the dispatcher's own
      lifecycle state: it raises DispatcherError unless the
      dispatcher's self-tracked state is RUNNING. This mirrors
      Scheduler.tick() (008), WorkflowEngine.execute() (010), and
      ConversationManager.receive() (011) exactly - dispatch() is
      IntentDispatcher's one "do real work" method, and per ADR-0002's
      now-four-data-point pattern, that is precisely the kind of
      method IService's start()/stop() docstring describes gating.
      register_mapping/remove_mapping/resolve/list_mappings remain
      ungated, matching every prior package's registry-operations
      precedent.

Non-Responsibilities:
    - IntentDispatcher contains no workflow logic and no intent
      parsing logic: it never imports argus.workflow.engine,
      argus.intent.router, or argus.intent.parser, and no intent name
      branches into service-specific code anywhere in this module
      (only into a table-driven Action lookup). The single exception
      is an isinstance(action, WorkflowAction) check used solely to
      decide whether to publish WorkflowSelected - this reads
      WorkflowAction's own workflow_id property, already computed by
      WorkflowAction itself, and calls nothing on IWorkflowEngine
      directly. dispatch() delegates execution exclusively through
      Action.execute(), never through IWorkflowEngine.execute()
      directly - see argus/dispatcher/action.py for where that actual
      IWorkflowEngine call lives.
    - No AI, no LLM, no networking, no persistence, no plugins, no
      retries, per the work order's explicit Version 1 Constraints.
      dispatch() runs entirely within the calling thread and returns
      only once the resolved Action's execute() call has returned or
      raised.

Dependencies:
    argus.events (Event, EventType, IEventBus), argus.lifecycle
    (LifecycleState), argus.intent.intent (Intent, IntentType),
    argus.dispatcher (Action, WorkflowAction, IIntentDispatcher, and
    the dispatcher exceptions).
"""

from types import MappingProxyType
from typing import Any, Dict, Mapping, Optional

from argus.dispatcher.action import Action, WorkflowAction
from argus.dispatcher.exceptions import (
    ActionExecutionError,
    DispatcherError,
    DuplicateMappingError,
    InvalidActionError,
    InvalidIntentError,
    MappingNotFoundError,
    NoMappingError,
)
from argus.dispatcher.interfaces import IIntentDispatcher
from argus.events.event import Event
from argus.events.event_types import EventType
from argus.events.interfaces import IEventBus
from argus.intent.intent import Intent, IntentType
from argus.lifecycle.lifecycle import LifecycleState


class IntentDispatcher(IIntentDispatcher):
    """
    In-memory, synchronous implementation of IIntentDispatcher.

    Purpose:
        Translate a resolved Intent into an executable Action via a
        configurable mapping table, and delegate execution to that
        Action, without the dispatcher itself knowing what kind of
        Action it is beyond its `kind` label. See the module docstring
        for the full design rationale.

    Dependencies:
        An IEventBus implementation, injected by the caller
        (bootstrap.py). Notably, IntentDispatcher does NOT take an
        IWorkflowEngine - see the module docstring's
        Non-Responsibilities. Any workflow_engine dependency lives
        entirely inside whichever WorkflowAction instances are
        registered via register_mapping(), not in the dispatcher
        itself.
    """

    def __init__(self, event_bus: IEventBus) -> None:
        self._event_bus = event_bus
        self._state: LifecycleState = LifecycleState.CREATED
        self._mappings: Dict[IntentType, Action] = {}

    # -- IService -----------------------------------------------------

    def initialize(self) -> None:
        if self._state != LifecycleState.CREATED:
            raise DispatcherError(
                f"Cannot initialize: IntentDispatcher is {self._state.name}, expected CREATED."
            )
        self._state = LifecycleState.INITIALIZING

    def start(self) -> None:
        if self._state != LifecycleState.INITIALIZING:
            raise DispatcherError(
                f"Cannot start: IntentDispatcher is {self._state.name}, expected INITIALIZING."
            )
        self._state = LifecycleState.RUNNING

    def stop(self) -> None:
        if self._state != LifecycleState.RUNNING:
            raise DispatcherError(
                f"Cannot stop: IntentDispatcher is {self._state.name}, expected RUNNING."
            )
        self._state = LifecycleState.STOPPING
        self._state = LifecycleState.STOPPED

    def status(self) -> LifecycleState:
        return self._state

    # -- IIntentDispatcher: registry operations (unaffected by lifecycle state) --

    def register_mapping(self, intent_name: IntentType, action: Action) -> None:
        if not isinstance(intent_name, IntentType):
            raise InvalidIntentError(
                f"intent_name must be an IntentType, got {intent_name!r}."
            )
        if not isinstance(action, Action):
            raise InvalidActionError(f"action must be an Action, got {action!r}.")
        if intent_name in self._mappings:
            raise DuplicateMappingError(
                f"Intent {intent_name.name} already has a registered Action; "
                "call remove_mapping() first to replace it."
            )
        self._mappings[intent_name] = action

    def remove_mapping(self, intent_name: IntentType) -> None:
        if not isinstance(intent_name, IntentType):
            raise InvalidIntentError(
                f"intent_name must be an IntentType, got {intent_name!r}."
            )
        if intent_name not in self._mappings:
            raise MappingNotFoundError(
                f"No Action is registered for intent {intent_name.name}."
            )
        del self._mappings[intent_name]

    def resolve(self, intent: Intent) -> Action:
        if not isinstance(intent, Intent):
            raise InvalidIntentError(f"resolve() requires an Intent, got {intent!r}.")
        try:
            return self._mappings[intent.name]
        except KeyError:
            raise NoMappingError(
                f"No Action is registered for intent {intent.name.name}."
            ) from None

    def list_mappings(self) -> Mapping[IntentType, Action]:
        return MappingProxyType(dict(self._mappings))

    # -- IIntentDispatcher: dispatch (gated on the dispatcher's own RUNNING state) --

    def dispatch(
        self, intent: Intent, *, context: Optional[Mapping[str, Any]] = None
    ) -> Mapping[str, Any]:
        if self._state != LifecycleState.RUNNING:
            raise DispatcherError(
                f"Cannot dispatch: IntentDispatcher is {self._state.name}, expected RUNNING."
            )
        if not isinstance(intent, Intent):
            raise InvalidIntentError(f"dispatch() requires an Intent, got {intent!r}.")

        self._publish(
            EventType.INTENT_DISPATCHED,
            {"intent_id": intent.id, "intent_name": intent.name.value},
        )

        try:
            action = self.resolve(intent)
        except DispatcherError as error:
            self._publish_failed(intent, "resolve", str(error))
            raise

        self._publish(
            EventType.ACTION_RESOLVED,
            {
                "intent_id": intent.id,
                "intent_name": intent.name.value,
                "action_kind": action.kind,
            },
        )

        if isinstance(action, WorkflowAction):
            self._publish(
                EventType.WORKFLOW_SELECTED,
                {
                    "intent_id": intent.id,
                    "intent_name": intent.name.value,
                    "workflow_id": action.workflow_id,
                },
            )

        self._publish(
            EventType.DISPATCH_STARTED,
            {"intent_id": intent.id, "intent_name": intent.name.value},
        )

        try:
            result = action.execute(context=context)
        except Exception as error:
            wrapped = ActionExecutionError(
                f"Action execution failed for intent {intent.name.value!r}: {error}"
            )
            self._publish_failed(intent, "execute", str(wrapped))
            raise wrapped from error

        self._publish(
            EventType.DISPATCH_COMPLETED,
            {"intent_id": intent.id, "intent_name": intent.name.value},
        )
        return result

    # -- internals ------------------------------------------------------

    def _publish_failed(self, intent: Intent, stage: str, message: str) -> None:
        self._publish(
            EventType.DISPATCH_FAILED,
            {
                "intent_id": intent.id,
                "intent_name": intent.name.value,
                "stage": stage,
                "error": message,
            },
        )

    def _publish(self, event_type: EventType, payload: Dict[str, Any]) -> None:
        self._event_bus.publish(
            Event(type=event_type, source="intent_dispatcher", payload=payload)
        )
