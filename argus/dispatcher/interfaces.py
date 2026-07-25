"""
Public interface contract for the ArgusOS Intent Dispatcher.

Purpose:
    Define IIntentDispatcher, the contract other modules depend on,
    per factory/packages/012_INTENT_DISPATCHER.md. IIntentDispatcher
    inherits IService, per this package's explicit requirement -
    IntentDispatcher is the fifth class in this codebase (after
    Scheduler, IntentRouter, WorkflowEngine, and ConversationManager)
    to implement it. See this package's IMPLEMENTATION_REPORT.md for
    a note on how IntentDispatcher's IService adoption compares to
    its four predecessors.

Responsibilities:
    - IIntentDispatcher: register_mapping / remove_mapping / resolve /
      dispatch / list_mappings, plus the inherited initialize / start
      / stop / status from IService.

Non-Responsibilities:
    - This module implements no behavior; see
      argus.dispatcher.dispatcher.IntentDispatcher.

Dependencies:
    argus.lifecycle.interfaces (IService), argus.intent.intent
    (Intent, IntentType), argus.dispatcher.action (Action).
"""

from abc import abstractmethod
from typing import Any, Mapping, Optional

from argus.dispatcher.action import Action
from argus.intent.intent import Intent, IntentType
from argus.lifecycle.interfaces import IService


class IIntentDispatcher(IService):
    """
    Mapping-and-delegation contract for ArgusOS's deterministic
    intent-to-action infrastructure.

    Purpose:
        Let a resolved Intent be translated into an executable Action
        and delegated for execution, without the dispatcher itself
        parsing intents, executing workflows, or performing any AI
        reasoning.
    """

    @abstractmethod
    def register_mapping(self, intent_name: IntentType, action: Action) -> None:
        """Register `action` as the Action to resolve to for every
        Intent whose name is `intent_name`. Raises InvalidIntentError
        if intent_name is not an IntentType. Raises InvalidActionError
        if action is not an Action instance. Raises
        DuplicateMappingError if intent_name already has a registered
        Action - call remove_mapping() first to replace it. Not
        affected by the dispatcher's own IService lifecycle state; a
        registry operation, not "active work.\""""

    @abstractmethod
    def remove_mapping(self, intent_name: IntentType) -> None:
        """Remove the Action currently registered for `intent_name`.
        Raises InvalidIntentError if intent_name is not an IntentType.
        Raises MappingNotFoundError if intent_name has no registered
        Action. Not affected by the dispatcher's own IService
        lifecycle state, matching register_mapping()."""

    @abstractmethod
    def resolve(self, intent: Intent) -> Action:
        """Return the Action currently registered for `intent`'s name,
        without executing it. Raises InvalidIntentError if intent is
        not an Intent instance. Raises NoMappingError if intent's name
        has no registered Action. A pure lookup; publishes no event
        and is not affected by the dispatcher's own IService lifecycle
        state, matching get_workflow() (Package 010) and
        active_session() (Package 011)."""

    @abstractmethod
    def dispatch(
        self, intent: Intent, *, context: Optional[Mapping[str, Any]] = None
    ) -> Mapping[str, Any]:
        """Resolve `intent` to its registered Action and delegate
        execution to it, returning the Action's own execution result.
        Raises DispatcherError if the dispatcher's own IService state
        is not RUNNING - dispatch() is IntentDispatcher's single "do
        real work" method, gated the same way Scheduler.tick()
        (Package 008), WorkflowEngine.execute() (Package 010), and
        ConversationManager.receive() (Package 011) are gated. Raises
        InvalidIntentError if intent is not an Intent instance. Raises
        NoMappingError if intent's name has no registered Action
        (propagated from resolve()). Raises ActionExecutionError,
        wrapping the underlying failure, if the resolved Action's
        execute() call raises. Publishes, in order: IntentDispatched,
        ActionResolved, WorkflowSelected (only if the resolved Action
        is a WorkflowAction), DispatchStarted, and then either
        DispatchCompleted (on success) or DispatchFailed (instead of
        DispatchCompleted, on any failure after IntentDispatched)."""

    @abstractmethod
    def list_mappings(self) -> Mapping[IntentType, Action]:
        """Return a read-only snapshot of every currently registered
        IntentType -> Action mapping. A pure lookup; publishes no
        event and is not affected by the dispatcher's own IService
        lifecycle state, matching resolve()."""
