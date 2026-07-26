"""
Exceptions raised by the ArgusOS Cognitive Pipeline.

Purpose:
    Give callers explicit, catchable failure modes for pipeline
    lifecycle transitions, malformed input, and delegated-call
    failures, per the coding standard's "raise meaningful
    exceptions... never silently ignore errors" and
    factory/packages/025_COGNITIVE_PIPELINE.md.

Responsibilities:
    - Provide a general pipeline-subsystem error base (also used
      directly for IService lifecycle transition failures, mirroring
      KnowledgeGraphError's (018), ReasoningError's (020), and
      DecisionError's (021) identical role), and more specific
      subtypes for "invalid request" and "a delegated call failed"
      failures.

Non-Responsibilities:
    - These exceptions carry no behavior beyond a message; they do
      not log, retry, or recover.

Dependencies:
    None.
"""


class PipelineError(Exception):
    """Base exception for the Cognitive Pipeline. Raised directly for
    failures that are not one of the more specific subtypes below, for
    example an invalid IService lifecycle transition, or calling
    run() while the pipeline's own state is not RUNNING."""


class InvalidPipelineRequestError(PipelineError):
    """Raised when run() is given something that is not a
    PipelineRequest instance, or a PipelineRequest whose `conversation`
    field is not a ConversationSession instance."""


class PipelineExecutionError(PipelineError):
    """Raised when a component the pipeline delegates to - in Version
    1, only Planner.plan_session() - raises during orchestration.
    Wraps the underlying exception (`raise ... from error`); no
    partial PipelineResult is ever returned. Mirrors
    RuleEvaluationError's (Package 021) identical "wrap a delegate's
    own raised exception" shape."""
