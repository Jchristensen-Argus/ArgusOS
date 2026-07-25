"""
Exceptions raised by the ArgusOS Workflow Engine.

Purpose:
    Give callers explicit, catchable failure modes for workflow
    registration and execution, per the coding standard's "explicit
    exceptions instead of silent failures" and
    factory/packages/010_WORKFLOW_ENGINE.md.

Responsibilities:
    - Provide a general workflow-subsystem error base, and more
      specific subtypes for "not found", "duplicate", "invalid
      input", and "step execution failed" failures, so callers can
      catch either the broad or the precise failure mode.

Non-Responsibilities:
    - These exceptions carry no behavior beyond a message; they do not
      log, retry, or recover.

Dependencies:
    None.
"""


class WorkflowError(Exception):
    """Base exception for the workflow subsystem. Raised directly for
    failures that are not one of the more specific subtypes below,
    such as an illegal lifecycle transition, executing a workflow
    engine that is not RUNNING, executing a workflow that is not
    PENDING, or cancelling a workflow that is not PENDING."""


class WorkflowNotFoundError(WorkflowError):
    """Raised when execute(), cancel(), or get_workflow() references a
    workflow_id with no corresponding registered workflow."""


class DuplicateWorkflowError(WorkflowError):
    """Raised when register_workflow() is called with a workflow_id
    that is already registered."""


class InvalidWorkflowError(WorkflowError):
    """Raised when register_workflow() is given invalid input: an
    empty name, an empty steps sequence, a step that is not a
    WorkflowStep, or a step whose action is not callable."""


class WorkflowExecutionError(WorkflowError):
    """Raised internally by WorkflowEngine when a step's action raises
    during execute(). Wraps the step's original exception (via
    `raise ... from error`, preserving the traceback chain). This
    exception is caught within execute() itself and never propagates
    to execute()'s caller: per factory/packages/010_WORKFLOW_ENGINE.md,
    a failing step publishes WorkflowFailed, marks the workflow
    FAILED, and stops execution - it does not raise out of execute().
    See WorkflowEngine._run_steps."""
