"""
Public interface contract for the ArgusOS Intent Dispatcher.

Purpose:
    Define IIntentDispatcher, the contract other modules depend on,
    per factory/packages/012_INTENT_DISPATCHER.md, as revised by
    factory/packages/013_CAPABILITY_REGISTRY.md. IIntentDispatcher
    inherits IService, per Package 012's explicit requirement -
    IntentDispatcher is the fifth class in this codebase (after
    Scheduler, IntentRouter, WorkflowEngine, and ConversationManager)
    to implement it.

Responsibilities:
    - IIntentDispatcher: resolve / dispatch, plus the inherited
      initialize / start / stop / status from IService.

Non-Responsibilities:
    - This module implements no behavior; see
      argus.dispatcher.dispatcher.IntentDispatcher.
    - As of Package 013, this interface no longer declares
      register_mapping / remove_mapping / list_mappings: capability
      registration is now argus.capability.interfaces.
      ICapabilityRegistry's responsibility, not the dispatcher's - see
      factory/packages/013_CAPABILITY_REGISTRY.md's "The Intent
      Dispatcher should no longer own knowledge of available
      capabilities" and this package's IMPLEMENTATION_REPORT.md for
      the full rationale.

Dependencies:
    argus.lifecycle.interfaces (IService), argus.intent.intent
    (Intent), argus.capability.capability (Capability, resolve()'s
    return type as of Package 013).
"""

from abc import abstractmethod
from typing import Any, Mapping, Optional

from argus.capability.capability import Capability
from argus.intent.intent import Intent
from argus.lifecycle.interfaces import IService


class IIntentDispatcher(IService):
    """
    Capability-resolution-and-delegation contract for ArgusOS's
    deterministic intent-to-action infrastructure.

    Purpose:
        Let a resolved Intent be resolved to a Capability, translated
        into an executable Action, and delegated for execution,
        without the dispatcher itself parsing intents, storing
        capability metadata, executing workflows, or performing any
        AI reasoning.
    """

    @abstractmethod
    def resolve(self, intent: Intent) -> Capability:
        """Return the Capability currently resolved for `intent`'s
        name, without building or executing an Action. Raises
        InvalidIntentError if intent is not an Intent instance. Raises
        NoCapabilityError if no enabled Capability is registered (in
        the injected ICapabilityRegistry) for intent's name. When
        multiple enabled Capabilities are registered for the same
        IntentType, resolve() deterministically returns the first
        match in the Capability Registry's own registration order -
        see argus.dispatcher.dispatcher.IntentDispatcher.resolve()'s
        docstring for this selection policy, which the Capability
        Registry itself does not apply (see
        ICapabilityRegistry.find_by_intent_type()'s docstring). A pure
        lookup; publishes no event and is not affected by the
        dispatcher's own IService lifecycle state, matching
        get_workflow() (Package 010) and active_session() (Package
        011)."""

    @abstractmethod
    def dispatch(
        self, intent: Intent, *, context: Optional[Mapping[str, Any]] = None
    ) -> Mapping[str, Any]:
        """Resolve `intent` to its Capability, build or obtain the
        Action that Capability describes, and delegate execution to
        it, returning the Action's own execution result. Raises
        DispatcherError if the dispatcher's own IService state is not
        RUNNING - dispatch() is IntentDispatcher's single "do real
        work" method, gated the same way Scheduler.tick() (Package
        008), WorkflowEngine.execute() (Package 010), and
        ConversationManager.receive() (Package 011) are gated. Raises
        InvalidIntentError if intent is not an Intent instance. Raises
        NoCapabilityError if intent's name has no registered, enabled
        Capability (propagated from resolve()). Raises
        ActionExecutionError, wrapping the underlying failure, if
        either building the Action from the resolved Capability or
        that Action's own execute() call raises. Publishes, in order:
        IntentDispatched, ActionResolved (carrying both the resolved
        capability_id and the built Action's kind), WorkflowSelected
        (only if the built Action is a WorkflowAction), DispatchStarted,
        and then either DispatchCompleted (on success) or
        DispatchFailed (instead of DispatchCompleted, on any failure
        after IntentDispatched)."""
