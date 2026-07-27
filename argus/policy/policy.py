"""
The Policy value object for the ArgusOS Policy Framework.

Purpose:
    Represent a single, immutable constraint, preference, or piece of
    governance that may eventually influence future execution - "A
    Policy defines constraints, preferences, or governance that
    influence future execution" - per
    factory/packages/040_POLICY_FRAMEWORK.md. Policies answer one
    question: "Under what rules should Argus operate?" This package
    introduces the Policy model only - no enforcement, no execution,
    no Policy Engine, no AI integration. No ownership relationship to
    Workspace/Project/Goal/Plan/Task/Capability is implemented yet;
    see "Future Relationship" below.

Every Field Defaults - Policy() Is Always Valid:
    Policy has its own dedicated PolicyBuilder - the same "value
    object with a dedicated builder" shape Project (036), Workspace
    (037), Goal (038), and DecisionRecord (039) all use, each of which
    lets every field default and leaves construction-time validation
    to the builder's own with_*() methods (see builder.py's own module
    docstring). `policy_id` defaults to a fresh uuid4 string, `name`
    and `description` both default to `""`, `status` defaults to
    `PolicyStatus.ACTIVE`, `scope` defaults to `PolicyScope.GLOBAL`,
    `metadata` defaults to a fresh `PolicyMetadata()`. `Policy()` with
    no arguments is therefore always valid.

name/description, Not title/question:
    Unlike DecisionRecord (039, which uses `title`/`question`), this
    package's own explicit field list reads "policy_id, name,
    description, status, scope, metadata" - `name`/`description`,
    matching Project's/Workspace's/Goal's own vocabulary. A Policy's
    own defining content is a rule or constraint, better captured as a
    named, described thing than as a question.

A Sixth Field - scope - Not Present On Project Or Workspace:
    Like `priority` on Goal (038), `scope` is a genuinely new
    top-level field, declared between `status` and `metadata` -
    continuing the "insert a new non-collection field before metadata,
    so metadata stays the last-declared field" positioning already
    used at Packages 030/031/038. This package's own explicit field
    list names it directly - not an inference.

No Validation Here - See builder.py:
    Like every other value object in this codebase, Policy performs no
    validation of its own fields - it has no `__post_init__` at all.

Future Relationship - A Policy May Eventually Govern Workspaces,
Projects, Goals, Plans, Tasks, Capabilities, Automations, the Decision
Engine, AI Model Selection, Approval Workflows:
    Per this package's own explicit "Future Relationship" section:
    "Document these only. Do NOT implement them." Policy therefore
    holds no field referencing any of these in Version 1 - no
    `governs` collection, no enforcement hook of any kind.

Responsibilities:
    - Policy: hold identity (`policy_id`), a human-readable `name` and
      `description`, its own `status` and `scope`, and descriptive
      `PolicyMetadata`, as an immutable value object.

Non-Responsibilities:
    - Policy performs no enforcement, evaluation, execution, or AI of
      any kind - "Policy is a passive domain object only."
    - Policy governs nothing in Version 1 - see "Future Relationship"
      above.
    - This module depends only on argus.policy.status (PolicyStatus),
      argus.policy.scope (PolicyScope), and argus.policy.metadata
      (PolicyMetadata) to type its own fields. It has no dependency on
      argus.policy.builder, matching the "pure, dependency-free leaf"
      precedent set by every other value object in this codebase.

Dependencies:
    argus.policy.status (PolicyStatus), argus.policy.scope
    (PolicyScope), argus.policy.metadata (PolicyMetadata).
"""

import uuid
from dataclasses import dataclass, field

from argus.policy.metadata import PolicyMetadata
from argus.policy.scope import PolicyScope
from argus.policy.status import PolicyStatus


@dataclass(frozen=True)
class Policy:
    """
    An immutable record of one constraint, preference, or piece of
    governance. See the module docstring for the full field
    semantics.

    Fields:
        policy_id: Unique identifier for this Policy. Defaults to a
            fresh uuid4 string.
        name: A short, human-readable label for this Policy. Defaults
            to an empty string.
        description: A longer, human-readable elaboration of what this
            Policy governs. Defaults to an empty string.
        status: This Policy's current PolicyStatus. Defaults to
            PolicyStatus.ACTIVE.
        scope: This Policy's current PolicyScope. Defaults to
            PolicyScope.GLOBAL.
        metadata: Descriptive bookkeeping about this Policy. Defaults
            to a fresh PolicyMetadata.
    """

    policy_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    status: PolicyStatus = PolicyStatus.ACTIVE
    scope: PolicyScope = PolicyScope.GLOBAL
    metadata: PolicyMetadata = field(default_factory=PolicyMetadata)
