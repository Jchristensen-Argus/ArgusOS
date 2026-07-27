"""
The Goal value object for the ArgusOS Goal Framework.

Purpose:
    Represent a single, immutable desired outcome within a Project -
    per factory/packages/038_GOAL_FRAMEWORK.md. "A Goal represents a
    desired outcome within a Project. Projects own Goals. Goals own
    Plans. Plans own Tasks. Goals are passive domain objects only."
    This package introduces the Goal model only - no ownership
    relationship to Project (above) or Plan (below) is implemented
    yet, and no field on Goal references either; see "Future
    Relationship" below. This package completes the one remaining gap
    in the organizational hierarchy above the execution pipeline -
    `Workspace -> Project -> Goal -> Plan -> Task` - unlike Packages
    036 and 037, which each extended the hierarchy from its own
    topmost end.

Every Field Defaults - Goal() Is Always Valid:
    Goal has its own dedicated GoalBuilder - the same "value object
    with a dedicated builder" shape CognitiveContext (022),
    PlanningSession (023), ExecutionTrace (028), Task (029),
    TaskRelationship (031), ExecutionResult (032),
    CapabilityExecutionResult (034), CapabilityContext (035), Project
    (036), and Workspace (037) all use, each of which lets every field
    default and leaves construction-time validation to the builder's
    own with_*() methods (see builder.py's own module docstring).
    `goal_id` defaults to a fresh uuid4 string, `name` and
    `description` both default to `""`, `status` defaults to
    `GoalStatus.PLANNING`, `priority` defaults to
    `GoalPriority.NORMAL`, `metadata` defaults to a fresh
    `GoalMetadata()`. `Goal()` with no arguments is therefore always
    valid, representing an empty, unnamed goal - `GoalBuilder` is the
    supported way to construct a genuinely populated one.

A Sixth Field - priority - Not Present On Project Or Workspace:
    Unlike `Project`/`Workspace` (each holding exactly `*_id`, `name`,
    `description`, `status`, `metadata` - five fields), `Goal` holds a
    sixth: `priority: GoalPriority`, declared between `status` and
    `metadata` - continuing the "insert a new non-collection field
    before metadata, so metadata stays the last-declared field"
    positioning already used for collection fields at Packages 030/031
    (`Plan.tasks`/`Task.relationships`), applied here to a scalar enum
    field instead. This is the work order's own explicit field list
    for this package - "goal_id, name, description, status, priority,
    metadata" - not an inference; no prior organizational-tier value
    object (`Project`, `Workspace`) has ever needed a priority field,
    since neither package's own work order named one.

No Validation Here - See builder.py:
    Like every other value object in this codebase, Goal performs no
    validation of its own fields - it has no `__post_init__` at all,
    mirroring `Project`'s/`Workspace`'s own identical shape, since it
    holds no sequence field of its own needing tuple-coercion.
    `GoalBuilder`'s own `with_name()`/`with_description()`/
    `with_status()`/`with_priority()`/`with_metadata()` methods are
    where malformed input is rejected - see builder.py's own module
    docstring.

Future Relationship - A Goal Will Eventually Own Plans, Success
Metrics, Milestones, Decisions, Deadlines, Risks, Dependencies:
    Per this package's own explicit "Future Relationship" section: "A
    Goal will eventually own: Plans, Success metrics, Milestones,
    Decisions, Deadlines, Risks, Dependencies. Do NOT implement these
    relationships. Document them only." Goal therefore holds no field
    referencing any of these in Version 1 - no `plans` collection, no
    `milestones` collection, and so on. A future package would most
    likely add such a field the same way `Task` gained `relationships`
    in Package 031: a new, defaulted, ordered collection field,
    declared after `priority` and before `metadata`, with a
    corresponding `with_<relationship>()`/`with_<relationship>s()`/
    `clear_<relationship>s()` trio added to GoalBuilder, mirroring
    TaskBuilder's own shape. This is a documented expectation about a
    future package's own likely shape, not a commitment this package
    makes.

Responsibilities:
    - Goal: hold identity (`goal_id`), a human-readable `name` and
      `description`, its own `status` and `priority`, and descriptive
      `GoalMetadata`, as an immutable value object.

Non-Responsibilities:
    - Goal performs no reasoning, scheduling, dispatch, or execution
      of any kind - "Goals are passive domain objects only."
    - Goal owns no Plans, Success metrics, Milestones, Decisions,
      Deadlines, Risks, or Dependencies in Version 1 - see "Future
      Relationship" above.
    - This module depends only on argus.goal.status (GoalStatus),
      argus.goal.priority (GoalPriority), and argus.goal.metadata
      (GoalMetadata) to type its own fields. It has no dependency on
      argus.goal.builder, matching the "pure, dependency-free leaf"
      precedent set by every other value object in this codebase.

Dependencies:
    argus.goal.status (GoalStatus), argus.goal.priority
    (GoalPriority), argus.goal.metadata (GoalMetadata).
"""

import uuid
from dataclasses import dataclass, field

from argus.goal.metadata import GoalMetadata
from argus.goal.priority import GoalPriority
from argus.goal.status import GoalStatus


@dataclass(frozen=True)
class Goal:
    """
    An immutable record of one desired outcome within a Project. See
    the module docstring for the full field semantics.

    Fields:
        goal_id: Unique identifier for this Goal. Defaults to a fresh
            uuid4 string.
        name: A short, human-readable label for this Goal. Defaults to
            an empty string.
        description: A longer, human-readable elaboration of what this
            Goal represents. Defaults to an empty string.
        status: This Goal's current GoalStatus. Defaults to
            GoalStatus.PLANNING.
        priority: This Goal's current GoalPriority. Defaults to
            GoalPriority.NORMAL.
        metadata: Descriptive bookkeeping about this Goal. Defaults to
            a fresh GoalMetadata.
    """

    goal_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    status: GoalStatus = GoalStatus.PLANNING
    priority: GoalPriority = GoalPriority.NORMAL
    metadata: GoalMetadata = field(default_factory=GoalMetadata)
