"""
Exceptions for the ArgusOS Execution Trace package.

Purpose:
    Define the error types argus.trace itself can raise. Per
    factory/packages/028_EXECUTION_TRACE.md, the Execution Trace is a
    "first-class architectural object," not logging/telemetry - its
    own errors are therefore genuine domain errors (malformed trace
    steps, illegal builder usage), not I/O or transport failures.

Responsibilities:
    - TraceError: the base exception for this package.
    - InvalidTraceStepError: raised by TraceBuilder.with_step() when
      given a malformed component/action/metadata argument.

Non-Responsibilities:
    - This module performs no logic beyond defining exception types -
      it holds no state and makes no decisions about when to raise.

Dependencies:
    None.
"""


class TraceError(Exception):
    """Base exception for the argus.trace package."""


class InvalidTraceStepError(TraceError):
    """Raised when TraceBuilder.with_step() is given a malformed
    component, action, or metadata argument."""
