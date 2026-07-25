"""
The Execution value object and ExecutionStatus enumeration for the
ArgusOS Agent Runtime.

Purpose:
    Represent a single, immutable snapshot of "one run of one Plan" -
    identity, progress, collected step results, and timing - per
    factory/packages/016_AGENT_RUNTIME.md. An Execution is pure data:
    it does not execute anything itself, does not dispatch, and does
    not call plugins or workflows - AgentRuntime
    (argus/runtime/runtime.py) is the only component that advances an
    Execution's state, and does so by constructing new Execution
    instances via dataclasses.replace, never by mutating an existing
    one - matching the precedent set by WorkflowEngine's treatment of
    Workflow (Package 010) and Planner's treatment of Plan (Package
    015).

Scope Note (Package Structure):
    This package's explicit file list
    (`__init__.py, runtime.py, execution.py, interfaces.py,
    exceptions.py`) has no separate status module, unlike
    `argus.workflow.state.WorkflowState`'s own separate file (Package
    010). ExecutionStatus is defined here, alongside Execution itself,
    matching the precedent Package 015 already set for
    `PlanStatus`/`Plan` living in one `plan.py` module - a deliberate,
    minor structural choice, not an oversight.

State Ownership:
    Planner owns Plans. AgentRuntime owns Executions. One Plan may
    eventually have multiple Executions (for example, re-running a
    Plan after a prior failed attempt) - the two concepts are
    deliberately not merged: Execution references its Plan only by
    `plan_id` (a plain string), never by holding a live Plan
    reference, mirroring Capability's own `workflow_id: Optional[str]`
    field (Package 013) referencing a Workflow by id only.

Responsibilities:
    - ExecutionStatus: the closed set of execution states an
      Execution may be in (CREATED, RUNNING, PAUSED, FAILED,
      COMPLETED, CANCELLED).
    - Execution: hold identity (id), the id of the Plan it is
      executing (plan_id), its current ExecutionStatus, its progress
      through the Plan's steps (current_step, a 0-based index of the
      next step to dispatch), the results collected so far
      (results, keyed by PlanStep id), when it started and completed
      running, and arbitrary caller metadata. Auto-generate `id` when
      not supplied. Guarantee immutability (frozen dataclass) and
      prevent mutation of the `results` and `metadata` mappings after
      construction.

Non-Responsibilities:
    - Execution does not validate its own fields, does not know how
      to advance `current_step` or add to `results`, and does not
      check whether its own state transitions are legal - all of
      that is AgentRuntime's responsibility (matching the validation
      precedent set by Capability/Plugin/Plan: data objects across
      this codebase contain no business logic).
    - Execution does not construct, obtain, or reference any
      IIntentDispatcher, IPlanner, Action, or IPluginManager - it is
      pure, serializable-shaped data.

Dependencies:
    None (standard library only).
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping, Optional


class ExecutionStatus(Enum):
    """
    The closed set of states an Execution may be in.

    CREATED: the Execution's initial state, set the instant
        start_execution() constructs it, before dispatching any step.
    RUNNING: set immediately after CREATED, for the duration of
        start_execution()'s (or resume_execution()'s) synchronous step
        loop. Also restored by resume_execution() when continuing a
        PAUSED Execution.
    PAUSED: set by pause_execution() on a RUNNING Execution. Since
        Version 1 has no concurrency (see this package's Constraints),
        an Execution can only actually be observed as PAUSED between
        two separate top-level Runtime calls, or if a dispatched
        step's own action re-enters the Runtime to request a pause
        before returning - AgentRuntime's step loop checks its
        Execution's status after every step and stops immediately if
        it is no longer RUNNING, without treating that as a failure.
    FAILED: set when a dispatched step's Dispatcher.dispatch() call
        raises. Terminal - no further steps run, no retries, no
        rollback, per this package's explicit Failure Rules.
    COMPLETED: set when every step in the Plan has been dispatched
        successfully. Terminal.
    CANCELLED: set by cancel_execution() on a CREATED, RUNNING, or
        PAUSED Execution. Terminal - a caller-initiated stop, distinct
        from FAILED (an execution failure) and COMPLETED (a normal
        finish).
    """

    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    FAILED = "failed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class Execution:
    """
    An immutable record of one run of one Plan: its identity, current
    status, progress, and the results collected so far.

    Purpose:
        Let AgentRuntime (and any future caller) describe and inspect
        "how far has this run of this Plan gotten, and what happened"
        without any of it executing anything on its own - see the
        module docstring.

    Responsibilities:
        - Store plan_id, id, status, current_step, results,
          started_at, completed_at, and metadata.
        - Auto-generate `id` when not supplied, default `status` to
          ExecutionStatus.CREATED, `current_step` to 0, `results` and
          `metadata` to empty mappings, and `started_at`/
          `completed_at` to None, and make `results` and `metadata`
          immutable containers.

    Dependencies:
        None.
    """

    plan_id: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: ExecutionStatus = ExecutionStatus.CREATED
    current_step: int = 0
    results: Mapping[str, Any] = field(default_factory=dict)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Frozen dataclasses require object.__setattr__ during
        # __post_init__. Wrapping `results` and `metadata` in
        # MappingProxyType makes the containers themselves read-only,
        # not just the attribute reference - the same pattern used by
        # Plan.metadata (Package 015) and Plugin.metadata (Package
        # 014).
        object.__setattr__(self, "results", MappingProxyType(dict(self.results)))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))
