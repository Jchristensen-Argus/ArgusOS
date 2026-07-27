"""
The CapabilityExecutionStatus enumeration for the ArgusOS Capability
Executor.

Purpose:
    Represent the closed set of states a CapabilityExecutionResult may
    carry, per factory/packages/034_CAPABILITY_EXECUTOR.md. "No
    transition logic" - this module defines only the enumeration
    itself; nothing in argus.capability_executor moves a
    CapabilityExecutionResult from one CapabilityExecutionStatus to
    another. Mirrors ExecutionStatus's (032) / TaskStatus's (029) own
    shape: a plain `Enum` (not a `str` subclass), lowercase string
    values matching each member's name.

Only COMPLETED And NOT_FOUND Are Ever Produced In Version 1:
    Per this package's own explicit Resolution behavior: "If a
    Capability exists whose name exactly matches the Task name,
    return: status = COMPLETED. Otherwise return: status = NOT_FOUND."
    Read literally, not by analogy to what the member's own name might
    suggest - see builder.py's and executor.py's own module docstrings
    for why a successful match produces COMPLETED rather than the
    seemingly more descriptive RESOLVED. PENDING serves only as
    CapabilityExecutionResult's own pre-resolve() default, mirroring
    ExecutionResult.status's identical default role. RESOLVED and
    FAILED are reserved for a future package - RESOLVED for a
    distinct "found, not yet dispatched" phase this package does not
    yet distinguish from "done," and FAILED for a genuine resolution
    failure (for example, an ambiguous or malformed registry state)
    this package's own deterministic, single-outcome lookup never
    produces. No Version 1 code anywhere in argus.capability_executor
    ever constructs a CapabilityExecutionResult with RESOLVED, FAILED,
    or PENDING as its own returned status.

Responsibilities:
    - CapabilityExecutionStatus: enumerate the five states a
      CapabilityExecutionResult's own `status` field may hold.

Non-Responsibilities:
    - This module implements no transition logic, no validation of
      whether a given transition is legal, and no behavior of any
      kind beyond the enumeration itself.

Dependencies:
    None.
"""

from enum import Enum


class CapabilityExecutionStatus(Enum):
    """
    The closed set of states a CapabilityExecutionResult may be in.
    None of these states imply any transition logic - no Version 1
    code in this codebase moves a CapabilityExecutionResult between
    them.

    PENDING: CapabilityExecutionResult's own default state, before
        resolve() has produced a result - no Version 1 code ever
        returns a CapabilityExecutionResult in this state from
        resolve() itself.
    RESOLVED: reserved for a future package that distinguishes "a
        matching Capability was found" from "resolution is fully
        done" - no Version 1 code ever produces this state; a
        successful match produces COMPLETED instead, per this
        package's own explicit Resolution behavior.
    COMPLETED: the state resolve() produces when a Capability exists
        whose name exactly matches the Task name.
    FAILED: reserved for a future package that reports a genuine
        resolution failure - no Version 1 code ever produces this
        state.
    NOT_FOUND: the state resolve() produces when no Capability's name
        exactly matches the Task name.
    """

    PENDING = "pending"
    RESOLVED = "resolved"
    COMPLETED = "completed"
    FAILED = "failed"
    NOT_FOUND = "not_found"
