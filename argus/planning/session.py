"""
The PlanningSession value object for ArgusOS.

Purpose:
    Represent a single, immutable snapshot of one planning cycle - the
    CognitiveContext it operates over, the goals and constraints that
    cycle carries, the Tasks it has been given (Package 030), and
    descriptive metadata - per factory/packages/023_PLANNING_SESSION.md,
    as amended by factory/packages/030_PLAN_TASK_INTEGRATION.md. "A
    Planning Session represents a single planning cycle... It
    performs no planning. It executes no workflows. It is a transport
    object only." A PlanningSession is pure data: it performs no
    planning, invokes no Planner, validates no goal, optimizes
    nothing, executes no workflow, and calls no other service - it
    only carries a CognitiveContext plus this cycle's own goals,
    constraints, tasks, and metadata forward.

Package 030 Amendment - tasks Joins goals/constraints:
    Per this package's own "New architecture" diagram - "Plan ->
    Goals / Constraints / Metadata / Tasks" - PlanningSession gained a
    fourth ordered collection field, `tasks: Sequence[Task]`, holding
    the immutable `Task` objects (Package 029) this planning cycle has
    been given, defaulting to an empty tuple, duplicate-free by
    `task_id`. Like `goals`/`constraints`, `tasks` holds the actual
    `Task` objects directly, not reference strings - the same "objects,
    not references" choice this module's own docstring already
    explains for `goals`/`constraints`. PlanningSession never
    generates, decomposes, or validates the Tasks it is given - see
    builder.py's own module docstring for where `with_task()`/
    `with_tasks()`'s duplicate-`task_id` validation actually lives.

Objects, Not References - A Deliberate Contrast With Package 022:
    Every field here holds an actual object, never a bare identifier
    string: `cognitive_context` holds the live, already-immutable
    `CognitiveContext` (Package 022) itself, and `goals`/`constraints`
    hold the actual `PlanningGoal`/`PlanningConstraint` objects, not
    reference strings pointing at them elsewhere. This is a deliberate
    contrast with `CognitiveContext`'s own three "..._references"
    fields (`memory_references`/`knowledge_references`/
    `decision_references`, Package 022), which deliberately hold bare
    identifier strings instead of live objects - and the distinction
    is resolved the same way it was there: by the work order's own
    field naming. Package 022's work order named three fields
    "...references" and one "...results," and this package's work
    order names no field "...references" at all - "goals" and
    "constraints" read the same way "reasoning_results" and
    "matched_rules" (Package 020/021) already do in this codebase:
    the actual objects, held directly. Holding the live
    `CognitiveContext` also costs nothing extra in the way holding a
    live `MemoryRecord`/`Entity`/`Decision` would have for Package
    022's fields - `CognitiveContext` is already fully immutable, so
    "shall NOT mutate contained objects" is true by construction
    here exactly as it was there, just by a different route (an
    unmutatable object rather than a bare string with nothing to
    mutate).

No Validation Here - See builder.py:
    Like every other value object in this codebase, PlanningSession
    performs no validation of its own fields in __post_init__ beyond
    the standard mutable-to-immutable wrapping (list/tuple -> tuple).
    PlanningSessionBuilder (builder.py) validates its own accumulated
    input before `build()` assembles a PlanningSession from it - the
    same "validation lives in the builder, not the value object"
    division of responsibility `argus.context.builder.ContextBuilder`
    (Package 022) established for `CognitiveContext`. PlanningSession
    remains directly constructible without going through
    PlanningSessionBuilder at all, for the same reason every other
    value object in this codebase is: a pure data holder should not
    force callers through one particular construction path.

Responsibilities:
    - PlanningSession: hold a CognitiveContext, this planning cycle's
      goals, constraints, and tasks, and descriptive metadata as a
      single immutable value object.

Non-Responsibilities:
    - PlanningSession performs no planning, goal validation, plan
      optimization, or workflow execution of any kind - see this
      package's own Objective and Constraints.
    - PlanningSession is not consumed by the Planner in Version 1 -
      "Package 023 introduces the abstraction only." See
      factory/packages/023_PLANNING_SESSION.md's own Version 1
      Limitations.
    - This module depends only on argus.context.context
      (CognitiveContext), argus.planning.goal (PlanningGoal),
      argus.planning.constraint (PlanningConstraint),
      argus.planning.metadata (PlanningMetadata), and argus.task.task
      (Task, Package 030) to type its own fields - it has no
      dependency on argus.planning.builder, matching the "pure,
      dependency-free leaf" precedent set by every other value object
      in this codebase.

Dependencies:
    argus.context.context (CognitiveContext),
    argus.planning.goal (PlanningGoal),
    argus.planning.constraint (PlanningConstraint),
    argus.planning.metadata (PlanningMetadata),
    argus.task.task (Task).
"""

import uuid
from dataclasses import dataclass, field
from typing import Optional, Sequence

from argus.context.context import CognitiveContext
from argus.planning.constraint import PlanningConstraint
from argus.planning.goal import PlanningGoal
from argus.planning.metadata import PlanningMetadata
from argus.task.task import Task


@dataclass(frozen=True)
class PlanningSession:
    """
    An immutable transport object carrying one planning cycle's
    CognitiveContext, goals, constraints, and metadata. See the module
    docstring for the full field semantics.

    Fields:
        session_id: Unique identifier for this PlanningSession.
            Defaults to a fresh uuid4 string.
        cognitive_context: The CognitiveContext this planning cycle
            operates over. Defaults to None (a session need not be
            tied to any CognitiveContext - see the "empty session"
            test scenarios in tests/test_planning_session.py).
        goals: The PlanningGoal objects this planning cycle carries.
            Defaults to an empty tuple.
        constraints: The PlanningConstraint objects this planning
            cycle carries. Defaults to an empty tuple.
        tasks: The Task objects (Package 029) this planning cycle has
            been given. Defaults to an empty tuple. Duplicate-free by
            `task_id` - see builder.py's own module docstring for
            where that validation is enforced.
        metadata: Descriptive bookkeeping about this PlanningSession
            itself (creation timestamp, schema version, correlation
            id, and arbitrary extra data). Defaults to a fresh
            PlanningMetadata.
    """

    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    cognitive_context: Optional[CognitiveContext] = None
    goals: Sequence[PlanningGoal] = field(default_factory=tuple)
    constraints: Sequence[PlanningConstraint] = field(default_factory=tuple)
    tasks: Sequence[Task] = field(default_factory=tuple)
    metadata: PlanningMetadata = field(default_factory=PlanningMetadata)

    def __post_init__(self) -> None:
        object.__setattr__(self, "goals", tuple(self.goals))
        object.__setattr__(self, "constraints", tuple(self.constraints))
        object.__setattr__(self, "tasks", tuple(self.tasks))
