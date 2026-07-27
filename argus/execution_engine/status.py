"""
The ExecutionStatus enumeration for the ArgusOS Execution Engine.

Purpose:
    Represent the closed set of states an ExecutionResult may carry,
    per factory/packages/032_EXECUTION_ENGINE.md. "No transition
    logic" - this module defines only the enumeration itself; nothing
    in argus.execution_engine moves an ExecutionResult from one
    ExecutionStatus to another. Mirrors TaskStatus's (029) /
    PlanStatus's own shape: a plain `Enum` (not a `str` subclass),
    lowercase string values matching each member's name.

No Transitions, No Behavior:
    No Version 1 code anywhere in argus.execution_engine ever
    constructs an ExecutionResult with any status other than
    ExecutionStatus.COMPLETED - "For Package 032: Every Task is
    considered successfully processed... Set: ExecutionStatus.
    COMPLETED." RUNNING, FAILED, and CANCELLED are reserved for a
    future package that introduces genuine task execution outcomes;
    PENDING serves only as ExecutionResult's own pre-execute()
    default. Transition rules (what follows PENDING, what makes an
    execution RUNNING, and so on) are explicitly out of scope for this
    package - "This package establishes lifecycle only."

Responsibilities:
    - ExecutionStatus: enumerate the five states an ExecutionResult's
      own `status` field may hold.

Non-Responsibilities:
    - This module implements no transition logic, no validation of
      whether a given transition is legal, and no behavior of any
      kind beyond the enumeration itself.

Dependencies:
    None.
"""

from enum import Enum


class ExecutionStatus(Enum):
    """
    The closed set of states an ExecutionResult may be in. None of
    these states imply any transition logic - no Version 1 code in
    this codebase moves an ExecutionResult between them.

    PENDING: ExecutionResult's own default state, before execute()
        has produced a result - no Version 1 code ever returns an
        ExecutionResult in this state from execute() itself.
    RUNNING: reserved for a future package that reports execution
        genuinely in progress - no Version 1 code ever produces this
        state.
    COMPLETED: the state execute() always produces in Version 1 -
        "Every Task is considered successfully processed."
    FAILED: reserved for a future package that reports a genuine
        execution failure - no Version 1 code ever produces this
        state.
    CANCELLED: reserved for a future package that reports an
        execution was withdrawn before completion - no Version 1 code
        ever produces this state.
    """

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
