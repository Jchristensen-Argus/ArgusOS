"""
Action and WorkflowAction for the ArgusOS Intent Dispatcher.

Purpose:
    Represent "the executable thing a resolved Capability maps to," in
    a way that lets IntentDispatcher invoke it without knowing what
    kind of Action it is, per
    factory/packages/012_INTENT_DISPATCHER.md and
    factory/packages/013_CAPABILITY_REGISTRY.md.

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
    - build_action_from_capability: translates a Capability's metadata
      (action_kind, workflow_id) into a constructed Action instance.
      Added by Package 013 as the "instantiate/obtain Action" step of
      IntentDispatcher.dispatch() - see that package's work order.
      This function, not IntentDispatcher itself, is where a
      Capability's action_kind is interpreted, and it is the only
      place in this module that imports argus.capability - a plain
      data-type dependency, not a service dependency (see
      argus/capability/capability.py: Capability holds no live service
      reference of its own).

Non-Responsibilities:
    - Action declares no constructor and holds no state; only concrete
      subclasses do. This lets a future PluginAction, AgentAction, or
      ConnectorAction be added by implementing this same one-method
      contract against whatever backend it needs (a plugin runner, an
      agent client, a connector client) - each is free to take
      whatever dependencies its own execute() requires, without
      IntentDispatcher or this module changing at all. Considered
      renaming Action to ActionBase/IAction while making this change
      (per Package 013's explicit "you MAY rename... ONLY if it
      meaningfully improves the architecture" allowance) and decided
      against it: Action's one-method contract is completely
      unaffected by Package 013's refactor - only *where* an Action
      gets constructed changed (build_action_from_capability, called
      by IntentDispatcher via an injected factory, instead of
      bootstrap.py registering pre-built Actions directly) - so a
      rename here would have been cosmetic only, which Package 013's
      own instruction explicitly rules out.
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
      responsibility, not any individual Action's or
      build_action_from_capability's - the factory function itself
      only translates an *unsupported action_kind* into
      InvalidActionError; it does not catch WorkflowAction
      construction failures beyond that, and does not catch execute()
      failures at all (it never calls execute()).

Dependencies:
    argus.dispatcher.exceptions (InvalidActionError), argus.workflow
    (IWorkflowEngine), argus.capability.capability (Capability, for
    build_action_from_capability's parameter type only - a data
    dependency, not a service dependency). Action itself has no
    dependencies beyond the standard library.
"""

from abc import ABC, abstractmethod
from typing import Any, Mapping, Optional

from argus.capability.capability import Capability
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

def build_action_from_capability(
    capability: Capability, *, workflow_engine: IWorkflowEngine
) -> Action:
    """
    Translate a Capability's metadata into a constructed Action.

    Purpose:
        Be the one place a Capability's action_kind is interpreted -
        IntentDispatcher itself never inspects action_kind directly,
        per factory/packages/013_CAPABILITY_REGISTRY.md's "Intent
        Dispatcher: Resolves capabilities and dispatches Actions"
        boundary. Called by IntentDispatcher only indirectly, via an
        injected `action_factory` callable bootstrap.py builds from
        this function (functools.partial'd with a concrete
        workflow_engine) - dispatcher.py itself never imports this
        function, IWorkflowEngine, or WorkflowAction, preserving the
        zero-argus.workflow-dependency property established in
        Package 012.

    Parameters:
        capability: The resolved Capability to build an Action for.
        workflow_engine: The IWorkflowEngine a "workflow" capability's
            resulting WorkflowAction will delegate to.

    Returns:
        A constructed Action instance ready for execute() to be
        called on it.

    Raises:
        InvalidActionError if capability.action_kind is not a
        supported action kind. Version 1 supports only "workflow"
        (WorkflowAction.kind). Also propagates whatever
        WorkflowAction's own constructor raises (InvalidActionError,
        for a malformed workflow_id or workflow_engine - see
        WorkflowAction.__init__).
    """
    if capability.action_kind == WorkflowAction.kind:
        return WorkflowAction(
            workflow_id=capability.workflow_id, workflow_engine=workflow_engine
        )
    raise InvalidActionError(
        f"No Action can be built for action_kind {capability.action_kind!r} "
        f"(capability {capability.id!r}) - Version 1 supports only "
        f"{WorkflowAction.kind!r}."
    )
