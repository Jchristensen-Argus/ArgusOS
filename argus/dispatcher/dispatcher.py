"""
IntentDispatcher: deterministic capability-resolution-and-delegation
for the ArgusOS Intent Dispatcher.

Purpose:
    Implement IIntentDispatcher: resolve a resolved Intent to a
    Capability via an injected ICapabilityRegistry, obtain the Action
    that Capability describes via an injected action_factory, and
    delegate execution to that Action - never to IWorkflowEngine or
    any other backend directly, and never by holding its own
    knowledge of what capabilities exist - per
    factory/packages/012_INTENT_DISPATCHER.md, as revised by
    factory/packages/013_CAPABILITY_REGISTRY.md.

Responsibilities:
    - resolve: query the injected ICapabilityRegistry for every
      Capability supporting an Intent's name, and deterministically
      select the first *enabled* match, in the registry's own
      registration order. This selection policy - "first enabled
      match wins" - lives here, not in the Capability Registry (see
      ICapabilityRegistry.find_by_intent_type()'s own docstring: it is
      a pure filter with no enabled/disabled policy and no selection
      between multiple matches). A pure lookup; not affected by the
      dispatcher's own IService lifecycle state, matching the
      precedent set by Scheduler's schedule/cancel/pause/resume
      (Package 008), WorkflowEngine's register_workflow/cancel/
      get_workflow (Package 010), and ConversationManager's
      start_session/end_session/history/active_session (Package 011).
    - dispatch: resolve an Intent to its Capability, call the injected
      action_factory to obtain an Action for it, and call that
      Action's own execute() method - the dispatcher never inspects,
      constructs, or reasons about what the Action actually does
      beyond calling execute() on it and, for a WorkflowAction
      specifically, reading its workflow_id to publish
      WorkflowSelected (see the module's Non-Responsibilities for why
      this one exception exists, unchanged from Package 012).
      Publishes IntentDispatched, ActionResolved (capability_id and
      action_kind), WorkflowSelected (WorkflowAction only),
      DispatchStarted, and then DispatchCompleted or DispatchFailed,
      per IIntentDispatcher.dispatch()'s docstring.
    - initialize / start / stop / status, per the inherited IService
      contract. dispatch() *is* gated on the dispatcher's own
      lifecycle state: it raises DispatcherError unless the
      dispatcher's self-tracked state is RUNNING, unchanged from
      Package 012. resolve() remains ungated, matching every prior
      package's registry-operations precedent.

Non-Responsibilities:
    - As of Package 013, IntentDispatcher holds NO capability
      knowledge of its own - no internal IntentType -> Action mapping
      exists anywhere in this class. Every dispatch() call queries the
      injected ICapabilityRegistry live; nothing about "what
      capabilities exist" is cached, hard-coded, or registered
      directly on the dispatcher (Package 012's register_mapping /
      remove_mapping / list_mappings methods were removed from
      IIntentDispatcher for exactly this reason - see
      IMPLEMENTATION_REPORT.md).
    - IntentDispatcher contains no workflow logic and no intent
      parsing logic: it never imports argus.workflow (any submodule),
      argus.intent.router, or argus.intent.parser, and no intent name
      branches into service-specific code anywhere in this module
      (only into the injected action_factory callable, which
      dispatcher.py treats as opaque). The one exception, unchanged
      from Package 012, is an isinstance(action, WorkflowAction) check
      used solely to decide whether to publish WorkflowSelected - this
      reads WorkflowAction's own workflow_id property and calls
      nothing on IWorkflowEngine directly. WorkflowAction itself lives
      in this same package (argus.dispatcher.action), not in
      argus.workflow, so this check does not reintroduce a dependency
      on the execution backend - see argus/dispatcher/action.py for
      where the actual IWorkflowEngine dependency lives
      (build_action_from_capability, called only via the injected
      action_factory).
    - No AI, no LLM, no networking, no persistence, no plugins, no
      retries, per the work order's explicit Version 1 Constraints.
      dispatch() runs entirely within the calling thread and returns
      only once the resolved Action's execute() call has returned or
      raised.

Dependencies:
    argus.events (Event, EventType, IEventBus), argus.lifecycle
    (LifecycleState), argus.intent.intent (Intent), argus.capability
    (Capability, ICapabilityRegistry), argus.dispatcher (Action,
    WorkflowAction, IIntentDispatcher, and the dispatcher exceptions).
    Notably NOT argus.workflow - see this module's
    Non-Responsibilities.
"""

from typing import Any, Callable, Dict, Mapping, Optional

from argus.capability.capability import Capability
from argus.capability.interfaces import ICapabilityRegistry
from argus.dispatcher.action import Action, WorkflowAction
from argus.dispatcher.exceptions import (
    ActionExecutionError,
    DispatcherError,
    InvalidIntentError,
    NoCapabilityError,
)
from argus.dispatcher.interfaces import IIntentDispatcher
from argus.events.event import Event
from argus.events.event_types import EventType
from argus.events.interfaces import IEventBus
from argus.intent.intent import Intent
from argus.lifecycle.lifecycle import LifecycleState

# A dispatcher-injected translator from a resolved Capability to an
# executable Action. Deliberately a plain callable, not a class the
# dispatcher constructs or inspects - see the module docstring and
# argus/dispatcher/action.py's build_action_from_capability, the
# Version 1 function bootstrap.py partially applies to build this
# callable. This is what keeps dispatcher.py free of any
# argus.workflow import, matching the opaque-callable idiom already
# established by StepAction (Package 010) and ScheduledTask.callback
# (Package 008).
ActionFactory = Callable[[Capability], Action]


class IntentDispatcher(IIntentDispatcher):
    """
    In-memory, synchronous implementation of IIntentDispatcher.

    Purpose:
        Resolve a resolved Intent to a Capability via the injected
        ICapabilityRegistry, obtain the Action that Capability
        describes via the injected action_factory, and delegate
        execution to that Action, without the dispatcher itself
        knowing what kind of Action it is beyond its `kind` label, and
        without holding any capability knowledge of its own. See the
        module docstring for the full design rationale.

    Dependencies:
        An IEventBus, an ICapabilityRegistry, and an ActionFactory
        callable, all injected by the caller (bootstrap.py). Notably,
        IntentDispatcher does NOT take an IWorkflowEngine directly -
        see the module docstring's Non-Responsibilities. Any
        workflow_engine dependency lives entirely inside the injected
        action_factory (built by bootstrap.py from
        argus.dispatcher.action.build_action_from_capability), not in
        the dispatcher itself.
    """

    def __init__(
        self,
        event_bus: IEventBus,
        capability_registry: ICapabilityRegistry,
        action_factory: ActionFactory,
    ) -> None:
        self._event_bus = event_bus
        self._capability_registry = capability_registry
        self._action_factory = action_factory
        self._state: LifecycleState = LifecycleState.CREATED

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

    # -- IIntentDispatcher: resolve (pure lookup, unaffected by lifecycle state) --

    def resolve(self, intent: Intent) -> Capability:
        if not isinstance(intent, Intent):
            raise InvalidIntentError(f"resolve() requires an Intent, got {intent!r}.")

        candidates = self._capability_registry.find_by_intent_type(intent.name)
        for capability in candidates:
            if capability.enabled:
                return capability

        raise NoCapabilityError(
            f"No enabled capability is registered for intent {intent.name.name}."
        )

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
            capability = self.resolve(intent)
        except DispatcherError as error:
            self._publish_failed(intent, "resolve", str(error))
            raise

        try:
            action = self._action_factory(capability)
        except Exception as error:
            wrapped = ActionExecutionError(
                f"Could not build an Action for capability {capability.id!r} "
                f"(intent {intent.name.value!r}): {error}"
            )
            self._publish_failed(intent, "build", str(wrapped))
            raise wrapped from error

        self._publish(
            EventType.ACTION_RESOLVED,
            {
                "intent_id": intent.id,
                "intent_name": intent.name.value,
                "capability_id": capability.id,
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
