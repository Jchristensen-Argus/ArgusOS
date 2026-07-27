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
    - InvalidCapabilityContextReferenceError: raised when resolve()
      is given something that is not a CapabilityContext instance -
      Package 035's own new outer-parameter check, added when
      resolve()'s own signature changed from accepting a bare Task to
      accepting a CapabilityContext (035).
    - InvalidTaskReferenceError: raised when the CapabilityContext
      given to resolve() carries a `task` field that is not a Task
      instance - kept genuinely alive after Package 035's signature
      change by moving from validating the outer parameter directly
      (034) to validating the extracted `context.task` value (035),
      per this package's own two-layer validation design (see
      executor.py's own module docstring).
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


class InvalidCapabilityContextReferenceError(CapabilityExecutionError):
    """Raised when resolve() is given something that is not a
    CapabilityContext instance - Package 035's new outer-parameter
    check (see this module's own docstring)."""


class InvalidTaskReferenceError(CapabilityExecutionError):
    """Raised when the CapabilityContext given to resolve() carries a
    `task` field that is not a Task instance - "accept Task"
    (CapabilityExecutor Responsibility 1), validated on the extracted
    context.task value as of Package 035 (see this module's own
    docstring)."""


class InvalidCapabilityExecutionResultError(CapabilityExecutionError):
    """Raised when CapabilityExecutionResultBuilder's with_*()
    methods are given a malformed argument."""
