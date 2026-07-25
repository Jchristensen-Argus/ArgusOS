"""
Action and WorkflowAction for the ArgusOS Intent Dispatcher.

Purpose:
    Represent "the executable thing a resolved Intent maps to," in a
    way that lets IntentDispatcher invoke it without knowing what kind
    of Action it is, per factory/packages/012_INTENT_DISPATCHER.md.

Responsibilities:
    - Action: an abstract base class declaring the single method
      IntentDispatcher ever calls on any Action - execute() - plus a
      `kind` class attribute concrete subclasses use to identify
      themselves in event payloads (see dispatcher.py) without the
      dispatcher needing to inspect a subclass's type.
    - WorkflowAction: Version 1's only concrete Action. Wraps a
      workflow_id and delegates execute() to an injected
      IWorkflowEngine's own execute() method - the same public method
      ConversationManager (Package 011) already delegates to. Carries
      no workflow logic of its own.

Non-Responsibilities:
    - Action declares no constructor and holds no state; only concrete
      subclasses do. This lets a future PluginAction, AgentAction, or
      ConnectorAction be added by implementing this same one-method
      contract against whatever backend it needs (a plugin runner, an
      agent client, a connector client) - each is free to take
      whatever dependencies its own execute() requires, without
      IntentDispatcher or this module changing at all.
    - WorkflowAction does not register, cancel, or inspect workflows -
      it only calls execute() on a workflow_id assumed to already be
      registered elsewhere (bootstrap.py or another component),
      exactly matching the assumption ConversationManager.receive()
      already makes about workflow_id (see
      argus/conversation/manager.py's Non-Responsibilities).
    - WorkflowAction does not catch or translate exceptions raised by
      IWorkflowEngine.execute() (e.g. WorkflowNotFoundError,
      WorkflowError) - it lets them propagate. Translating a failed
      Action into a dispatcher-level failure (ActionExecutionError)
      and publishing DispatchFailed is IntentDispatcher's
      responsibility, not any individual Action's.

Dependencies:
    argus.dispatcher.exceptions (InvalidActionError), argus.workflow
    (IWorkflowEngine), for WorkflowAction only. Action itself has no
    dependencies beyond the standard library.
"""

from abc import ABC, abstractmethod
from typing import Any, Mapping, Optional

from argus.dispatcher.exceptions import InvalidActionError
from argus.workflow.interfaces import IWorkflowEngine


class Action(ABC):
    """
    Abstract base class for anything an Intent can be dispatched to.

    Purpose:
        Let IntentDispatcher delegate execution uniformly, regardless
        of what kind of Action is registered for a given intent name.

    Responsibilities:
        - Declare execute() as the one method every concrete Action
          must implement.
        - Provide `kind`, a short string identifying the Action's
          type for event payloads (see dispatcher.py's ActionResolved
          publication). Subclasses must override it; the base class
          value is deliberately generic and unused in practice.
    """

    kind: str = "action"

    @abstractmethod
    def execute(self, *, context: Optional[Mapping[str, Any]] = None) -> Mapping[str, Any]:
        """
        Perform this Action, given the current context.

        Parameters:
            context: An optional mapping of caller-supplied input.
                Concrete Actions decide what, if anything, to do with
                it (WorkflowAction passes it straight through to
                IWorkflowEngine.execute()).

        Returns:
            A mapping of execution results. The exact shape is
            defined by the concrete Action, not by this base class.

        Raises:
            Whatever the concrete Action's own backend raises;
            execute() does not catch or translate its own failures -
            see this module's Non-Responsibilities.
        """
        raise NotImplementedError


class WorkflowAction(Action):
    """
    Version 1's only concrete Action: delegates to an existing,
    already-registered Workflow via IWorkflowEngine.

    Purpose:
        Let IntentDispatcher map an intent name to a specific
        workflow_id without the dispatcher itself ever importing or
        calling IWorkflowEngine directly - see dispatcher.py's module
        docstring.

    Dependencies:
        An IWorkflowEngine implementation and the workflow_id to
        execute, both injected at construction (by whoever builds the
        mapping - bootstrap.py in Version 1).
    """

    kind = "workflow"

    def __init__(self, *, workflow_id: str, workflow_engine: IWorkflowEngine) -> None:
        if not isinstance(workflow_id, str) or not workflow_id:
            raise InvalidActionError(
                f"WorkflowAction requires a non-empty workflow_id string, got {workflow_id!r}."
            )
        if not isinstance(workflow_engine, IWorkflowEngine):
            raise InvalidActionError(
                f"WorkflowAction requires an IWorkflowEngine, got {workflow_engine!r}."
            )
        self._workflow_id = workflow_id
        self._workflow_engine = workflow_engine

    @property
    def workflow_id(self) -> str:
        return self._workflow_id

    def execute(self, *, context: Optional[Mapping[str, Any]] = None) -> Mapping[str, Any]:
        return self._workflow_engine.execute(self._workflow_id, context=context)
