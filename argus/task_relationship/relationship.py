"""
The TaskRelationship value object for the ArgusOS Task Relationships
package.

Purpose:
    Represent a single, immutable, purely descriptive relationship
    between two Tasks - per
    factory/packages/031_TASK_RELATIONSHIPS.md. "Extend the Task
    domain so that Tasks can describe immutable relationships with
    other Tasks. This package does not implement scheduling,
    execution, or dependency resolution. It only introduces the
    relationship model." "The relationship contains no logic. It is
    purely descriptive."

Every Field Defaults - TaskRelationship() Is Always Valid:
    TaskRelationship has its own dedicated RelationshipBuilder - the
    same "value object with a dedicated builder" shape
    CognitiveContext (022), PlanningSession (023), ExecutionTrace
    (028), and Task (029) all use, each of which lets every field
    default and leaves construction-time validation to the builder's
    own with_*() methods (see builder.py's own module docstring).
    `relationship_id` defaults to a fresh uuid4 string,
    `source_task`/`target_task` both default to `None`,
    `relationship_type` defaults to `RelationshipType.RELATED` (the
    most generic, non-committal member - see relationship_type.py's
    own module docstring), `metadata` defaults to a fresh
    `RelationshipMetadata()`. `TaskRelationship()` with no arguments
    is therefore always valid, representing an empty, unlinked
    relationship - `RelationshipBuilder` is the supported way to
    construct a genuinely populated one.

source_task/target_task Hold Objects, Not Reference Strings:
    Mirrors PlanningSession.cognitive_context (022/023) and
    Plan.tasks/PlanningSession.tasks (030) own "objects, not
    references" precedent: `source_task`/`target_task` hold the
    actual, already-immutable `Task` objects directly - the same
    resolution principle applied for the same reason, the work
    order's own field names ("source_task"/"target_task", not
    "source_task_id"/"target_task_reference").

Why source_task/target_task Default To None Rather Than Being
Required:
    TraceStep (028) makes its own `component`/`action` required, with
    no builder of its own, reasoning that "an empty placeholder string
    would misrepresent which stage occurred" - a comparable concern
    applies here: a TaskRelationship with no source_task/target_task
    is not a meaningful relationship. TraceStep and TaskRelationship
    nonetheless belong to different architectural families: TraceStep
    is a leaf item constructed directly by TraceBuilder.with_step(),
    with no dedicated builder of its own, while this package's own
    work order explicitly creates a standalone RelationshipBuilder -
    placing TaskRelationship in the same family as Task/
    PlanningSession/CognitiveContext/ExecutionTrace, every one of
    which lets every field default and relies entirely on its own
    builder for validation. Consistency with that family's own
    established convention - not TraceStep's - governs here; see
    factory/packages/031_TASK_RELATIONSHIPS.md's own "Engineering
    Decision" section for the full reasoning.

No Validation Here - See builder.py:
    Like every other value object in this codebase, TaskRelationship
    performs no validation of its own fields in `__post_init__`. Every
    RelationshipBuilder `with_*` method validates its argument before
    assigning it - see builder.py's own module docstring.

Responsibilities:
    - TaskRelationship: hold identity (`relationship_id`), the two
      Tasks it connects (`source_task`, `target_task`), its own
      `relationship_type`, and descriptive `RelationshipMetadata`, as
      an immutable value object.

Non-Responsibilities:
    - TaskRelationship performs no scheduling, dependency resolution,
      ordering, or execution of any kind - see this package's own
      Objective and Constraints.
    - TaskRelationship does not validate that `source_task` and
      `target_task` are distinct Tasks - a relationship referencing
      the same Task as both its source and target is not rejected;
      see factory/packages/031_TASK_RELATIONSHIPS.md's own Known
      Limitations.
    - This module depends only on argus.task.task (Task),
      argus.task_relationship.relationship_type (RelationshipType),
      and argus.task_relationship.metadata (RelationshipMetadata) to
      type its own fields.

Dependencies:
    argus.task.task (Task), argus.task_relationship.relationship_type
    (RelationshipType), argus.task_relationship.metadata
    (RelationshipMetadata).
"""

import uuid
from dataclasses import dataclass, field
from typing import Optional

from argus.task.task import Task
from argus.task_relationship.metadata import RelationshipMetadata
from argus.task_relationship.relationship_type import RelationshipType


@dataclass(frozen=True)
class TaskRelationship:
    """
    An immutable, purely descriptive relationship between two Tasks.
    See the module docstring for the full field semantics.

    Fields:
        relationship_id: Unique identifier for this relationship.
            Defaults to a fresh uuid4 string.
        source_task: The Task this relationship describes as its
            source. Defaults to None.
        target_task: The Task this relationship describes as its
            target. Defaults to None.
        relationship_type: This relationship's own RelationshipType.
            Defaults to RelationshipType.RELATED.
        metadata: Descriptive bookkeeping about this relationship.
            Defaults to a fresh RelationshipMetadata.
    """

    relationship_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_task: Optional[Task] = None
    target_task: Optional[Task] = None
    relationship_type: RelationshipType = RelationshipType.RELATED
    metadata: RelationshipMetadata = field(default_factory=RelationshipMetadata)
