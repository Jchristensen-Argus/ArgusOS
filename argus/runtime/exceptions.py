"""
Exceptions raised by the ArgusOS Agent Runtime.

Purpose:
    Give callers explicit, catchable failure modes for execution
    creation, progress, and lifecycle-state transitions, per the
    coding standard's "raise meaningful exceptions... never silently
    ignore errors" and factory/packages/016_AGENT_RUNTIME.md. Mirrors
    the exception hierarchy shape already established by
    argus.planner.exceptions (Package 015), argus.dispatcher.exceptions
    (Package 012), and argus.workflow.exceptions (Package 010).

Responsibilities:
    - Provide a general runtime-subsystem error base, and more
      specific subtypes for "invalid input," "not found," "invalid
      state transition," and "a dispatched step failed" failures.

Naming Note:
    The base class is named `AgentRuntimeError`, not `RuntimeError`,
    to avoid shadowing Python's own built-in `RuntimeError` - the same
    care already taken by every other exception module in this
    codebase to pick subsystem-qualified names.

Non-Responsibilities:
    - These exceptions carry no behavior beyond a message; they do
      not log, retry, or recover - Version 1 has no retry logic
      anywhere, per this package's explicit Constraints.

Dependencies:
    None.
"""


class AgentRuntimeError(Exception):
    """Base exception for the Agent Runtime subsystem. Raised directly
    for failures that are not one of the more specific subtypes
    below."""


class InvalidExecutionError(AgentRuntimeError):
    """Raised when start_execution() is given something that is not a
    Plan instance, or when any method is given something that is not
    the expected type (a non-string execution_id)."""


class ExecutionNotFoundError(AgentRuntimeError):
    """Raised when get_execution(), pause_execution(),
    resume_execution(), or cancel_execution() references an
    execution_id with no corresponding registered Execution."""


class InvalidExecutionStateError(AgentRuntimeError):
    """Raised when: start_execution() is given a Plan whose current,
    canonical PlanStatus (per the injected IPlanner) is not VALIDATED;
    pause_execution() is called on an Execution that is not RUNNING;
    resume_execution() is called on an Execution that is not PAUSED;
    cancel_execution() is called on an Execution that is already
    terminal (FAILED, COMPLETED, or CANCELLED); or start_execution()/
    resume_execution() is called while the Runtime's own IService
    lifecycle state is not RUNNING."""


class StepExecutionError(AgentRuntimeError):
    """Raised when a PlanStep's Dispatcher.dispatch() call raises.
    Wraps the underlying error; the triggering Execution is marked
    FAILED and persisted before this is raised - callers may inspect
    get_execution() afterward to see the failure."""
