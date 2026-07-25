"""
Exceptions raised by the ArgusOS Intent Dispatcher.

Purpose:
    Give callers explicit, catchable failure modes for mapping
    registration and dispatch, per the coding standard's "raise
    meaningful exceptions... never silently ignore errors" and
    factory/packages/012_INTENT_DISPATCHER.md.

Responsibilities:
    - Provide a general dispatcher-subsystem error base, and more
      specific subtypes for "invalid intent," "invalid action," "no
      mapping," "duplicate mapping," "mapping not found," and "action
      execution failed" failures, so callers can catch either the
      broad or the precise failure mode - matching the exception
      hierarchy shape already established by
      argus.workflow.exceptions and argus.conversation.exceptions.

Non-Responsibilities:
    - These exceptions carry no behavior beyond a message; they do
      not log, retry, or recover.

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
    not an Intent instance, or register_mapping()/remove_mapping() is
    given something that is not an IntentType."""


class InvalidActionError(DispatcherError):
    """Raised when register_mapping() is given something that is not
    an Action instance, or when a concrete Action (e.g. WorkflowAction)
    is constructed with invalid input."""


class NoMappingError(DispatcherError):
    """Raised by resolve() when no Action is currently registered for
    an Intent's name - for example, if a mapping was removed via
    remove_mapping() and never replaced."""


class DuplicateMappingError(DispatcherError):
    """Raised when register_mapping() is called for an IntentType that
    already has a registered Action. Callers must call remove_mapping()
    first to replace an existing mapping."""


class MappingNotFoundError(DispatcherError):
    """Raised when remove_mapping() is called for an IntentType with
    no currently registered Action."""


class ActionExecutionError(DispatcherError):
    """Raised by dispatch() when the resolved Action's execute() call
    raises. Wraps the original exception (via `raise ... from error`,
    preserving the traceback chain) so callers of IIntentDispatcher
    never need to know which concrete Action type - or which
    downstream service, such as IWorkflowEngine - actually failed."""
