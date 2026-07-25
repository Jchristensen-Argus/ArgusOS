"""
Exceptions raised by the ArgusOS Intent Dispatcher.

Purpose:
    Give callers explicit, catchable failure modes for capability
    resolution and dispatch, per the coding standard's "raise
    meaningful exceptions... never silently ignore errors" and
    factory/packages/012_INTENT_DISPATCHER.md and
    factory/packages/013_CAPABILITY_REGISTRY.md.

Responsibilities:
    - Provide a general dispatcher-subsystem error base, and more
      specific subtypes for "invalid intent," "invalid action," "no
      capability," and "action execution failed" failures, so callers
      can catch either the broad or the precise failure mode -
      matching the exception hierarchy shape already established by
      argus.workflow.exceptions and argus.conversation.exceptions.

Non-Responsibilities:
    - These exceptions carry no behavior beyond a message; they do
      not log, retry, or recover.
    - Failures specific to registering, unregistering, or looking up
      a Capability by id belong to argus.capability.exceptions, not
      here - as of Package 013, this module no longer owns any
      mapping-registration concept of its own (see this package's
      IMPLEMENTATION_REPORT.md for the removal of the Package 012
      register_mapping/remove_mapping surface and its
      DuplicateMappingError/MappingNotFoundError exceptions).

Dependencies:
    None.
"""


class DispatcherError(Exception):
    """Base exception for the dispatcher subsystem. Raised directly
    for failures that are not one of the more specific subtypes below,
    such as calling dispatch() while the IntentDispatcher is not
    RUNNING."""


class InvalidIntentError(DispatcherError):
    """Raised when resolve() or dispatch() is given something that is
    not an Intent instance."""


class InvalidActionError(DispatcherError):
    """Raised when a concrete Action (e.g. WorkflowAction) is
    constructed with invalid input, or when
    argus.dispatcher.action.build_action_from_capability is given a
    Capability whose action_kind has no supported Action to build."""


class NoCapabilityError(DispatcherError):
    """Raised by resolve() when no enabled Capability is currently
    registered in the Capability Registry for an Intent's name - for
    example, if every Capability supporting that IntentType is
    disabled, or none was ever registered. Named for what it reports
    (no capability was found to resolve to), replacing Package 012's
    NoMappingError now that capability ownership has moved to
    argus.capability.registry.CapabilityRegistry - see this package's
    IMPLEMENTATION_REPORT.md."""


class ActionExecutionError(DispatcherError):
    """Raised by dispatch() when either building an Action from the
    resolved Capability (via the injected action_factory) or calling
    that Action's execute() raises. Wraps the original exception (via
    `raise ... from error`, preserving the traceback chain) so callers
    of IIntentDispatcher never need to know which concrete Action type
    - or which downstream service, such as IWorkflowEngine - actually
    failed."""
