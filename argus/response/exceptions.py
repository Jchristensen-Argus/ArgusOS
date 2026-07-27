"""
Exceptions raised by the ArgusOS Response Engine package.

Purpose:
    Give callers explicit, catchable failure modes for ResponseEngine
    lifecycle transitions and malformed input, per the coding
    standard's "raise meaningful exceptions... never silently ignore
    errors" and factory/packages/027_RESPONSE_ENGINE.md.

Responsibilities:
    - Provide a general response-subsystem error base (also used
      directly for IService lifecycle transition failures, mirroring
      PipelineError's (025) and AgentError's (026) identical role),
      and a more specific subtype for "the Plan reference is invalid"
      failures.

Non-Responsibilities:
    - These exceptions carry no behavior beyond a message; they do
      not log, retry, or recover.
    - Unlike PipelineError's own PipelineExecutionError and AgentError's
      own AgentExecutionError, there is no "wrap a delegate's own
      exception" subtype here - ResponseEngine has no delegate. Its
      one public method, build_response(), calls no other live
      service; it either receives a valid Plan reference or it
      doesn't. See engine.py's own module docstring.

Dependencies:
    None.
"""


class ResponseError(Exception):
    """Base exception for the Response Engine. Raised directly for
    failures that are not the more specific subtype below, for example
    an invalid IService lifecycle transition."""


class InvalidPlanReferenceError(ResponseError):
    """Raised when build_response() is given something that is not a
    Plan instance - "Validate the Plan reference" (ResponseEngine
    Responsibility 2)."""
