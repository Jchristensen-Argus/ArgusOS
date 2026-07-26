"""
Exceptions raised by the ArgusOS Cognitive Context package.

Purpose:
    Give callers explicit, catchable failure modes for invalid
    ContextBuilder input, per the coding standard's "raise meaningful
    exceptions... never silently ignore errors" and
    factory/packages/022_COGNITIVE_CONTEXT.md. Mirrors the exception
    hierarchy shape already established by
    argus.decision.exceptions (Package 021) and
    argus.reasoning.exceptions (Package 020) - a single base plus
    narrow, specific subtypes.

Responsibilities:
    - Provide a general Cognitive Context error base, and a more
      specific subtype for invalid ContextBuilder input.

Non-Responsibilities:
    - These exceptions carry no behavior beyond a message; they do
      not log, retry, or recover.
    - No lifecycle-state exception exists here, and ContextError is
      never raised for that reason - CognitiveContext and
      ContextBuilder are plain value objects with no IService
      lifecycle at all (see interfaces.py's own Architectural Note
      for why this package introduces no new core service).

Dependencies:
    None.
"""


class ContextError(Exception):
    """Base exception for the Cognitive Context package."""


class InvalidContextError(ContextError):
    """Raised when a ContextBuilder `with_*` method is given
    malformed input: an empty or non-string conversation/memory/
    knowledge/decision identifier, a non-ReasoningResult item passed
    to with_reasoning(), or a non-string/empty metadata key passed to
    with_metadata(). CognitiveContext itself performs no validation -
    see context.py's own module docstring - so this is only ever
    raised by ContextBuilder."""
