"""
The Workflow and WorkflowStep value objects for the ArgusOS Workflow
Engine.

Purpose:
    Represent a single, immutable orchestration unit - a named
    sequence of deterministic steps - and its progress through
    execution, per factory/packages/010_WORKFLOW_ENGINE.md.

Responsibilities:
    - WorkflowStep: pair a human-readable name with a deterministic
      action - a plain callable that receives the current context
      mapping and returns an updated context mapping. Steps carry no
      behavior of their own beyond this; WorkflowEngine is solely
      responsible for invoking them in order and reacting to failure.
    - Workflow: hold identity (id, name), progress (state, steps,
      created_at/started_at/completed_at), and caller-supplied
      metadata. Auto-generate `id` and `created_at` when not supplied.
      Guarantee immutability (frozen dataclass) and prevent mutation
      of the steps sequence or metadata mapping after construction.

Non-Responsibilities:
    - Neither class executes anything. WorkflowEngine
      (argus/workflow/engine.py) is the only component that invokes a
      WorkflowStep's action or advances a Workflow's state; it does so
      by constructing new Workflow instances via dataclasses.replace,
      never by mutating an existing one.

Dependencies:
    argus.workflow.state (WorkflowState).
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Callable, Mapping, Optional, Sequence

from argus.workflow.state import WorkflowState

# A step action receives the current context and returns the updated
# context. Deterministic by requirement (see the work order's
# "Workflow Steps" section): the same context must always produce the
# same result. WorkflowEngine imposes no base class on actions - they
# are plain callables, matching the precedent set by
# ScheduledTask.callback (Package 008) and IIntentRouter's registered
# handlers (Package 009).
StepAction = Callable[[Mapping[str, Any]], Mapping[str, Any]]


@dataclass(frozen=True)
class WorkflowStep:
    """
    A single named, deterministic unit of work within a Workflow.

    Purpose:
        Let WorkflowEngine identify which step is running (for event
        payloads and error messages) without inspecting the action
        callable itself.
    """

    name: str
    action: StepAction


@dataclass(frozen=True)
class Workflow:
    """
    An immutable record of a single orchestration run: its identity,
    its ordered steps, and its current progress through execution.

    Purpose:
        Represent "what should happen" (steps) and "what has happened
        so far" (state, started_at, completed_at) as one consistent,
        immutable snapshot, per factory/packages/010_WORKFLOW_ENGINE.md.

    Responsibilities:
        - Auto-generate `id` and `created_at` when not supplied.
        - Default `state` to WorkflowState.PENDING and `metadata` to
          an empty mapping.
        - Reject accidental mutation after construction (frozen
          dataclass) and prevent mutation of `steps` (wrapped in a
          tuple) or `metadata` (wrapped in MappingProxyType).

    Dependencies:
        None.
    """

    name: str
    steps: Sequence[WorkflowStep]
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    state: WorkflowState = WorkflowState.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Frozen dataclasses require object.__setattr__ to set fields,
        # including during __post_init__. Wrapping `steps` in a tuple
        # and `metadata` in MappingProxyType makes the containers
        # themselves read-only, not just the attribute reference -
        # the same pattern used by Intent.entities/parameters
        # (Package 009) and Event.payload/metadata (Package 003).
        object.__setattr__(self, "steps", tuple(self.steps))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))
