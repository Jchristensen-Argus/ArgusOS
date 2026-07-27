"""
Exceptions for the ArgusOS Execution Engine package.

Purpose:
    Give callers explicit, catchable failure modes for
    ExecutionEngine lifecycle transitions and malformed input, per
    the coding standard's "raise meaningful exceptions... never
    silently ignore errors" and
    factory/packages/032_EXECUTION_ENGINE.md.

Responsibilities:
    - ExecutionError: the base exception for this package (also used
      directly for IService lifecycle transition failures, mirroring
      ResponseError's (027) identical role).
    - InvalidPlanReferenceError: raised when execute() is given
      something that is not a Plan instance - mirrors
      InvalidPlanReferenceError's identical name and role in
      argus.response.exceptions (027).
    - InvalidExecutionResultError: raised by ExecutionResultBuilder's
      with_*() methods when given a malformed argument.

Non-Responsibilities:
    - These exceptions carry no behavior beyond a message; they do
      not log, retry, or recover.
    - Unlike PipelineError's own PipelineExecutionError and AgentError's
      own AgentExecutionError, there is no "wrap a delegate's own
      exception" subtype here - ExecutionEngine has no delegate. Its
      one public method, execute(), calls no other live service; it
      either receives a valid Plan reference or it doesn't, mirroring
      ResponseEngine's own identical reasoning (027).

Dependencies:
    None.
"""


class ExecutionError(Exception):
    """Base exception for the Execution Engine. Raised directly for
    failures that are not one of the more specific subtypes below, for
    example an invalid IService lifecycle transition."""


class InvalidPlanReferenceError(ExecutionError):
    """Raised when execute() is given something that is not a Plan
    instance - "validate Plan" (ExecutionEngine Responsibility 2)."""


class InvalidExecutionResultError(ExecutionError):
    """Raised when ExecutionResultBuilder's with_*() methods are
    given a malformed argument."""
