"""
The Workspace value object for the ArgusOS Workspace Framework.

Purpose:
    Represent a single, immutable highest-level organizational
    boundary within Argus - per
    factory/packages/037_WORKSPACE_FRAMEWORK.md. "A Workspace
    represents the highest-level organizational boundary within
    Argus" - examples given include "Joel Christensen, Deline Box &
    Display, Just Tallow, Family, Sandbox." "A Workspace owns
    Projects. Projects own Goals. Goals own Plans. Plans own Tasks."
    This package introduces the Workspace model only - no ownership
    relationship to Project (or anything else) is implemented yet;
    see "Future Relationship" below.

Every Field Defaults - Workspace() Is Always Valid:
    Workspace has its own dedicated WorkspaceBuilder - the same "value
    object with a dedicated builder" shape CognitiveContext (022),
    PlanningSession (023), ExecutionTrace (028), Task (029),
    TaskRelationship (031), ExecutionResult (032),
    CapabilityExecutionResult (034), CapabilityContext (035), and
    Project (036) all use, each of which lets every field default and
    leaves construction-time validation to the builder's own with_*()
    methods (see builder.py's own module docstring). `workspace_id`
    defaults to a fresh uuid4 string, `name` and `description` both
    default to `""`, `status` defaults to `WorkspaceStatus.ACTIVE`,
    `metadata` defaults to a fresh `WorkspaceMetadata()`. `Workspace()`
    with no arguments is therefore always valid, representing an
    empty, unnamed workspace - `WorkspaceBuilder` is the supported way
    to construct a genuinely populated one. Directly mirrors
    `Project`'s own shape (036) - `workspace_id`/`name`/`description`/
    `status`/`metadata` is exactly `Project`'s own `project_id`/
    `name`/`description`/`status`/`metadata`, one level up the
    ownership hierarchy.

No Validation Here - See builder.py:
    Like every other value object in this codebase, Workspace performs
    no validation of its own fields - it has no `__post_init__` at
    all, mirroring `Project`'s own identical shape, since it holds no
    sequence field of its own needing tuple-coercion.
    `WorkspaceBuilder`'s own `with_name()`/`with_description()`/
    `with_status()`/`with_metadata()` methods are where malformed
    input is rejected - see builder.py's own module docstring.

Future Relationship - A Workspace Will Eventually Own Projects, Users,
Shared Knowledge, Shared Assets, Automations, Credentials,
Configuration, Policies, Models, Memory:
    Per this package's own explicit "Future Relationship" section: "A
    Workspace will eventually own: Projects, Users, Shared Knowledge,
    Shared Assets, Automations, Credentials, Configuration, Policies,
    Models, Memory. Do NOT implement these relationships yet. Document
    them only." Workspace therefore holds no field referencing any of
    these in Version 1 - no `projects` collection, no `users`
    collection, and so on. A future package would most likely add such
    a field the same way `Task` gained `relationships` in Package 031:
    a new, defaulted, ordered collection field, declared after
    `status` and before `metadata` (continuing the "insert the new
    collection field before metadata, so metadata stays the
    last-declared field" precedent established at Package 030 and
    repeated at 031), with a corresponding
    `with_<relationship>()`/`with_<relationship>s()`/
    `clear_<relationship>s()` trio added to WorkspaceBuilder, mirroring
    TaskBuilder's own shape. This is a documented expectation about a
    future package's own likely shape, not a commitment this package
    makes or a field this package adds. Ten owned entity categories are
    named here, versus six for Project (036) - Workspace's own
    "highest-level organizational boundary" role names a
    broader set of concerns (identity, shared resources, automation,
    security, configuration) than Project's own narrower
    "long-running work" role.

Responsibilities:
    - Workspace: hold identity (`workspace_id`), a human-readable
      `name` and `description`, its own `status`, and descriptive
      `WorkspaceMetadata`, as an immutable value object.

Non-Responsibilities:
    - Workspace performs no reasoning, scheduling, dispatch, or
      execution of any kind - "Workspace is a passive domain object
      only."
    - Workspace owns no Projects, Users, Shared Knowledge, Shared
      Assets, Automations, Credentials, Configuration, Policies,
      Models, or Memory in Version 1 - see "Future Relationship"
      above.
    - This module depends only on argus.workspace.status
      (WorkspaceStatus) and argus.workspace.metadata
      (WorkspaceMetadata) to type its own fields. It has no dependency
      on argus.workspace.builder, matching the "pure, dependency-free
      leaf" precedent set by every other value object in this
      codebase.

Dependencies:
    argus.workspace.status (WorkspaceStatus), argus.workspace.metadata
    (WorkspaceMetadata).
"""

import uuid
from dataclasses import dataclass, field

from argus.workspace.metadata import WorkspaceMetadata
from argus.workspace.status import WorkspaceStatus


@dataclass(frozen=True)
class Workspace:
    """
    An immutable record of one highest-level organizational boundary
    within Argus. See the module docstring for the full field
    semantics.

    Fields:
        workspace_id: Unique identifier for this Workspace. Defaults
            to a fresh uuid4 string.
        name: A short, human-readable label for this Workspace (for
            example, "Just Tallow" or "Family"). Defaults to an empty
            string.
        description: A longer, human-readable elaboration of what this
            Workspace represents. Defaults to an empty string.
        status: This Workspace's current WorkspaceStatus. Defaults to
            WorkspaceStatus.ACTIVE.
        metadata: Descriptive bookkeeping about this Workspace.
            Defaults to a fresh WorkspaceMetadata.
    """

    workspace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    status: WorkspaceStatus = WorkspaceStatus.ACTIVE
    metadata: WorkspaceMetadata = field(default_factory=WorkspaceMetadata)
