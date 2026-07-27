"""
The Project value object for the ArgusOS Project Framework.

Purpose:
    Represent a single, immutable top-level organizational unit for
    long-running work - per factory/packages/036_PROJECT_FRAMEWORK.md.
    "A Project is the top-level organizational unit for long-running
    work" - examples given include "Just Tallow, Packaging Sales,
    ArgusOS, Book Publishing, Real Estate, Marketing, Personal."
    "Projects own Goals. Goals own Plans. Plans own Tasks." This
    package introduces the Project model only - no ownership
    relationship to Goal (or anything else) is implemented yet; see
    "Future Relationship" below.

Every Field Defaults - Project() Is Always Valid:
    Project has its own dedicated ProjectBuilder - the same "value
    object with a dedicated builder" shape CognitiveContext (022),
    PlanningSession (023), ExecutionTrace (028), Task (029),
    TaskRelationship (031), ExecutionResult (032),
    CapabilityExecutionResult (034), and CapabilityContext (035) all
    use, each of which lets every field default and leaves
    construction-time validation to the builder's own with_*()
    methods (see builder.py's own module docstring). `project_id`
    defaults to a fresh uuid4 string, `name` and `description` both
    default to `""`, `status` defaults to `ProjectStatus.PLANNING`,
    `metadata` defaults to a fresh `ProjectMetadata()`. `Project()`
    with no arguments is therefore always valid, representing an
    empty, unnamed project - `ProjectBuilder` is the supported way to
    construct a genuinely populated one. Directly mirrors Task's own
    shape (029) - `project_id`/`name`/`description`/`status`/
    `metadata` is exactly Task's own `task_id`/`name`/`description`/
    `status`/`metadata`, minus the `relationships` field Task gained
    in Package 031, since this package introduces no ownership
    relationships yet.

No Validation Here - See builder.py:
    Like every other value object in this codebase, Project performs
    no validation of its own fields in `__post_init__` - it has no
    `__post_init__` at all, since (unlike Task's `relationships` or
    CapabilityContextMetadata's `tags`) it holds no sequence field of
    its own needing tuple-coercion. `ProjectBuilder`'s own
    `with_name()`/`with_description()`/`with_status()`/`with_metadata()`
    methods are where malformed input is rejected - see builder.py's
    own module docstring.

Future Relationship - Projects Will Eventually Own Goals, Documents,
Knowledge, Conversations, Assets, Campaigns:
    Per this package's own explicit "Future Relationship" section:
    "Projects will eventually own: Goals, Documents, Knowledge,
    Conversations, Assets, Campaigns. Do not implement those
    relationships yet. Simply document them." Project therefore holds
    no field referencing any of these in Version 1 - no `goals`
    collection, no `documents` collection, and so on. A future package
    would most likely add such a field the same way Task gained
    `relationships` in Package 031: a new, defaulted, ordered
    collection field, declared after `status` and before `metadata`
    (continuing the "insert the new collection field before metadata,
    so metadata stays the last-declared field" precedent established
    at Package 030 and repeated at 031), with a corresponding
    `with_<relationship>()`/`with_<relationship>s()`/
    `clear_<relationship>s()` trio added to ProjectBuilder, mirroring
    TaskBuilder's own `with_relationship()`/`with_relationships()`/
    `clear_relationships()` shape. This is a documented expectation
    about a future package's own likely shape, not a commitment this
    package makes or a field this package adds.

Responsibilities:
    - Project: hold identity (`project_id`), a human-readable `name`
      and `description`, its own `status`, and descriptive
      `ProjectMetadata`, as an immutable value object.

Non-Responsibilities:
    - Project performs no reasoning, scheduling, dispatch, or
      execution of any kind - "Project is a passive domain object
      only."
    - Project owns no Goals, Documents, Knowledge, Conversations,
      Assets, or Campaigns in Version 1 - see "Future Relationship"
      above.
    - This module depends only on argus.project.status (ProjectStatus)
      and argus.project.metadata (ProjectMetadata) to type its own
      fields. It has no dependency on argus.project.builder, matching
      the "pure, dependency-free leaf" precedent set by every other
      value object in this codebase.

Dependencies:
    argus.project.status (ProjectStatus), argus.project.metadata
    (ProjectMetadata).
"""

import uuid
from dataclasses import dataclass, field

from argus.project.metadata import ProjectMetadata
from argus.project.status import ProjectStatus


@dataclass(frozen=True)
class Project:
    """
    An immutable record of one top-level organizational unit for
    long-running work. See the module docstring for the full field
    semantics.

    Fields:
        project_id: Unique identifier for this Project. Defaults to a
            fresh uuid4 string.
        name: A short, human-readable label for this Project (for
            example, "Just Tallow" or "ArgusOS"). Defaults to an empty
            string.
        description: A longer, human-readable elaboration of what
            this Project represents. Defaults to an empty string.
        status: This Project's current ProjectStatus. Defaults to
            ProjectStatus.PLANNING.
        metadata: Descriptive bookkeeping about this Project. Defaults
            to a fresh ProjectMetadata.
    """

    project_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    status: ProjectStatus = ProjectStatus.PLANNING
    metadata: ProjectMetadata = field(default_factory=ProjectMetadata)
