"""
Exceptions for the ArgusOS Capability Context package.

Purpose:
    Define the exception hierarchy raised by CapabilityContextBuilder's
    own validation - mirroring the exact shape of every sibling
    package's exceptions.py (see, most recently,
    argus.capability_executor.exceptions's own
    InvalidCapabilityExecutionResultError).

Hierarchy:
    CapabilityContextError
        Base exception for the argus.capability_context package. Never
        raised directly.
    InvalidCapabilityContextError(CapabilityContextError)
        Raised by CapabilityContextBuilder's with_task()/with_plan()/
        with_execution_trace() methods when given a malformed
        argument - see builder.py's own module docstring.

Naming Note - Distinct From
argus.capability_executor.exceptions.InvalidCapabilityContextReferenceError:
    That sibling exception, added by Package 035 to
    argus.capability_executor.exceptions, validates a different thing
    in a different package: whether the outer `context` argument
    CapabilityExecutor.resolve() receives is itself a CapabilityContext
    instance. This module's own InvalidCapabilityContextError instead
    validates the individual field values CapabilityContextBuilder is
    given (a Task, a Plan, an ExecutionTrace) before they are ever
    assembled into a CapabilityContext at all - the same "builder
    validates its own inputs" role InvalidCapabilityExecutionResultError
    (034) and InvalidExecutionResultError (032) already play for their
    own sibling builders. Deliberately named differently
    ("...ContextError," not "...ContextReferenceError") precisely to
    avoid the two being mistaken for the same exception across package
    boundaries.

Dependencies:
    None - this module depends only on Python's own Exception type.
"""


class CapabilityContextError(Exception):
    """Base exception for the argus.capability_context package."""


class InvalidCapabilityContextError(CapabilityContextError):
    """Raised by CapabilityContextBuilder's with_*() methods when
    given a malformed argument. See this module's own docstring for
    why this is named differently from
    argus.capability_executor.exceptions.InvalidCapabilityContextReferenceError."""
