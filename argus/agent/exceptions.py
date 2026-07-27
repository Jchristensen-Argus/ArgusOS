"""
Exceptions raised by the ArgusOS Agent Session package.

Purpose:
    Give callers explicit, catchable failure modes for AgentService
    lifecycle transitions, malformed input, and delegated-call
    failures, per the coding standard's "raise meaningful
    exceptions... never silently ignore errors" and
    factory/packages/026_AGENT_SESSION.md.

Responsibilities:
    - Provide a general agent-subsystem error base (also used
      directly for IService lifecycle transition failures, mirroring
      PipelineError's (025), KnowledgeGraphError's (018),
      ReasoningError's (020), and DecisionError's (021) identical
      role), and more specific subtypes for "invalid request" and "a
      delegated call failed" failures - the same two-subtype shape
      PipelineError's own package (025) established one layer below.

Non-Responsibilities:
    - These exceptions carry no behavior beyond a message; they do
      not log, retry, or recover.

Dependencies:
    None.
"""


class AgentError(Exception):
    """Base exception for the Agent Session package. Raised directly
    for failures that are not one of the more specific subtypes below,
    for example an invalid IService lifecycle transition, or calling
    run() while the service's own state is not RUNNING."""


class InvalidAgentRequestError(AgentError):
    """Raised when run() is given something that is not an
    AgentRequest instance, or an AgentRequest whose `session` field is
    not an AgentSession instance, or whose `conversation` field is not
    a ConversationSession instance."""


class AgentExecutionError(AgentError):
    """Raised when a component AgentService delegates to - in Version
    1, only CognitivePipeline.run() - raises during orchestration.
    Wraps the underlying exception (`raise ... from error`); no
    partial AgentResponse is ever returned. Mirrors
    PipelineExecutionError's (Package 025) identical "wrap a
    delegate's own raised exception" shape, which itself mirrors
    RuleEvaluationError's (Package 021)."""
