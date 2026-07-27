"""
Exceptions for the ArgusOS Capability Executor package.

Purpose:
    Give callers explicit, catchable failure modes for
    CapabilityExecutor dispatch and malformed input, per the coding
    standard's "raise meaningful exceptions... never silently ignore
    errors" and factory/packages/034_CAPABILITY_EXECUTOR.md.

Responsibilities:
    - CapabilityExecutionError: the base exception for this package
      (also used directly for IService lifecycle transition failures,
      mirroring ExecutionError's (032) identical role).
    - InvalidTaskReferenceError: raised when resolve() is given
      something that is not a Task instance - mirrors
      InvalidPlanReferenceError's identical name and role in
      argus.execution_engine.exceptions (032).
    - InvalidCapabilityExecutionResultError: raised by
      CapabilityExecutionResultBuilder's with_*() methods when given a
      malformed argument.

Non-Responsibilities:
    - These exceptions carry no behavior beyond a message; they do
      not log, retry, or recover.
    - No "wrap a delegate's own exception" subtype exists here -
      CapabilityExecutor's one live collaborator, CapabilityRegistry,
      is only ever asked a deterministic, always-answerable question
      (does a Capability with this name exist?) whose one documented
      failure mode, CapabilityNotFoundError, is treated as a normal
      resolution outcome (NOT_FOUND), not an error to wrap and
      re-raise.

Dependencies:
    None.
"""


class CapabilityExecutionError(Exception):
    """Base exception for the Capability Executor. Raised directly
    for failures that are not one of the more specific subtypes
    below, for example an invalid IService lifecycle transition."""


class InvalidTaskReferenceError(CapabilityExecutionError):
    """Raised when resolve() is given something that is not a Task
    instance - "accept Task" (CapabilityExecutor Responsibility 1)."""


class InvalidCapabilityExecutionResultError(CapabilityExecutionError):
    """Raised when CapabilityExecutionResultBuilder's with_*()
    methods are given a malformed argument."""
