"""
The Plan value object and PlanStatus enumeration for the ArgusOS
Planner.

Purpose:
    Represent a single, immutable snapshot of "how ArgusOS intends to
    satisfy one Intent" - an ordered sequence of PlanSteps and the
    planning-only state of that reasoning process - per
    factory/packages/015_PLANNER.md. A Plan is pure data: it does not
    execute anything, does not dispatch actions, and does not call
    plugins - execution remains entirely outside this package, per
    this package's explicit Objective.

Package 030 Amendment - tasks Joins steps:
    Per factory/packages/030_PLAN_TASK_INTEGRATION.md's own explicit
    "Extend the existing immutable: Plan. Add: tasks" instruction,
    Plan gained a fifth ordered collection field, `tasks: Sequence[Task]`
    - an ordered, immutable, duplicate-free (by `task_id`) collection
    of the immutable `Task` objects (Package 029) this Plan currently
    owns, defaulting to an empty tuple. `Task` describes work; `Plan`
    merely holds a reference to zero or more of them - "The Planner
    owns Tasks, but does not perform them." Like `steps`, `tasks` is
    never generated, decomposed, or otherwise derived by this package
    - Planner.create_plan()/plan_session() (argus.planner.planner)
    simply preserve whatever Tasks a caller (or an upstream
    PlanningSession) already supplied, per this package's own explicit
    "Do not generate tasks automatically" instruction. See
    planner.py's own module docstring for the exact validation
    (duplicate-`task_id` rejection) this field's "no duplicates"
    requirement is enforced by - Plan itself performs none, matching
    every other value object in this codebase.

Scope Note (Package Structure):
    This package's explicit file list
    (`__init__.py, planner.py, plan.py, step.py, interfaces.py,
    exceptions.py`) has no separate `status.py` module, unlike
    `argus.workflow.state.WorkflowState`'s own separate file (Package
    010). PlanStatus is defined here, alongside Plan itself, since the
    work order's own Domain Model section describes `status` as one of
    Plan's own fields rather than as an independent concept - a
    deliberate, minor structural choice, not an oversight.

Responsibilities:
    - PlanStatus: the closed set of planning-only states a Plan may be
      in (CREATED, VALIDATED, READY, FAILED, COMPLETED). No planner
      operation in Version 1 produces READY or COMPLETED - see this
      module's PlanStatus docstring and
      argus.planner.planner.Planner's own module docstring for why.
    - Plan: hold identity (id), the originating Intent, when it was
      created (created_at), its current planning status, its ordered
      PlanSteps, its ordered Tasks (Package 030), and arbitrary caller
      metadata. Auto-generate `id` and `created_at` when not supplied.
      Guarantee immutability (frozen dataclass) and prevent mutation of
      the `steps` sequence, `tasks` sequence, or `metadata` mapping
      after construction.

Non-Responsibilities:
    - Plan does not validate its own fields, does not enforce that its
      `steps` are contiguously ordered, does not check whether any
      step's required_capability exists anywhere, and does not reject
      duplicate `tasks` (by `task_id`) - all four are Planner's
      responsibility (matching the validation precedent set by
      Capability/Plugin/Workflow: data objects across this codebase
      contain no business logic).
    - Plan never executes, schedules, or decomposes any Task it holds
      - "This package does not execute tasks" (Package 030's own
      Objective) - `tasks` is inspected, never invoked.
    - Plan does not construct, obtain, or reference any
      ICapabilityRegistry, IIntentDispatcher, Action, or IPluginManager
      - it is pure, serializable-shaped data, and the Planner that
      produces it is completely unaware of plugins, per this
      package's explicit Plugin Integration guidance.

Dependencies:
    argus.intent.intent (Intent), for typing originating_intent.
    argus.planner.step (PlanStep), for typing steps.
    argus.task.task (Task), for typing tasks (Package 030).
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping, Sequence

from argus.intent.intent import Intent
from argus.planner.step import PlanStep
from argus.task.task import Task


class PlanStatus(Enum):
    """
    The closed set of planning-only states a Plan may be in. None of
    these states imply execution has happened or will happen
    automatically - per this package's Objective, "No execution
    occurs. These are planning states only."

    CREATED: the Plan's initial state, set by create_plan() and
        restored by any subsequent structural mutation (add_step(),
        remove_step(), reorder_steps()) - see
        argus.planner.planner.Planner's module docstring for why a
        structural mutation always resets status to CREATED.
    VALIDATED: set by validate_plan() when every non-optional
        PlanStep's required_capability is currently registered with
        the Capability Registry.
    READY: reserved for a future package that integrates the Planner
        with dispatch - no Version 1 Planner method ever produces
        this state. Included because the work order's Domain Model
        names it as a possible status value, matching the same
        "reserved for a future package" treatment Package 012 gave
        workflow_ids with no registered Workflow behind them yet.
    FAILED: set by validate_plan() when at least one non-optional
        PlanStep's required_capability is not currently registered
        with the Capability Registry - see
        argus.planner.exceptions.PlanValidationError.
    COMPLETED: reserved for a future package that reports execution
        outcomes back onto a Plan - no Version 1 Planner method ever
        produces this state, for the same reason as READY above.
    """

    CREATED = "created"
    VALIDATED = "validated"
    READY = "ready"
    FAILED = "failed"
    COMPLETED = "completed"


@dataclass(frozen=True)
class Plan:
    """
    An immutable record of one Execution Plan: the Intent it
    originated from, its ordered PlanSteps, and its current planning
    status.

    Purpose:
        Let the Planner (and any future caller further down the
        target architecture - the Capability Registry, the
        Dispatcher) describe and inspect "how ArgusOS intends to
        satisfy this Intent" without any of them executing anything -
        see the module docstring.

    Responsibilities:
        - Store originating_intent, id, status, created_at, steps,
          tasks, and metadata.
        - Auto-generate `id` and `created_at` when not supplied,
          default `status` to PlanStatus.CREATED and `steps`/`tasks`
          to an empty sequence, and make `steps`, `tasks`, and
          `metadata` immutable containers.

    Dependencies:
        None.
    """

    originating_intent: Intent
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: PlanStatus = PlanStatus.CREATED
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    steps: Sequence[PlanStep] = field(default_factory=tuple)
    tasks: Sequence[Task] = field(default_factory=tuple)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Frozen dataclasses require object.__setattr__ during
        # __post_init__. Wrapping `steps`/`tasks` in a tuple and
        # `metadata` in MappingProxyType makes the containers
        # themselves read-only, not just the attribute reference - the
        # same pattern used by Plugin.exported_capabilities/metadata
        # (Package 014) and Capability.intent_types/metadata (Package
        # 013). Duplicate-`task_id` rejection is not performed here -
        # see the module docstring's "Package 030 Amendment" note.
        object.__setattr__(self, "steps", tuple(self.steps))
        object.__setattr__(self, "tasks", tuple(self.tasks))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))
