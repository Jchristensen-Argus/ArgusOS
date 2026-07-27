"""
The ProjectMetadata value object for the ArgusOS Project Framework.

Purpose:
    Hold lightweight, descriptive bookkeeping about a single Project
    instance itself - when it was created, what schema version
    produced it, a correlation identifier for tracing it, who owns it,
    and what tags organize it - per
    factory/packages/036_PROJECT_FRAMEWORK.md. "Follow existing
    metadata conventions." ProjectMetadata is pure data: it does not
    compute anything and knows nothing about what a Project actually
    contains.

Reconciling "Suggested Fields" With Established Metadata Conventions -
A New Kind Of Divergence:
    This package's own field list is explicitly headed "Suggested
    fields" - not the imperative "Fields:" every prior metadata
    module's own work order used (028-035) - immediately signaling
    more latitude than usual. The list itself, "created_at, owner,
    tags, version, extra," diverges from every established metadata
    module in two ways at once: it omits `correlation_id`, present in
    every sibling metadata module since Package 028 without exception,
    and it introduces two genuinely new fields, `owner` and `tags`,
    that no metadata module has ever carried. Every prior "follow
    existing metadata conventions" instruction (029, 031, 032, 033,
    034, 035) only ever needed to resolve a *field-order* tension -
    the field *set* was always already identical to the established
    quartet. This is the first package where the suggested field set
    itself differs in composition, not merely order.

    Resolved by treating "Follow existing metadata conventions" as
    the dominant instruction (as it has been in every prior
    resolution) and "Suggested fields" as genuinely additive to that
    convention, not a replacement of it: `correlation_id` is kept,
    since dropping it would be a genuine convention break, not a
    conventions-preserving reordering; `owner` and `tags` are added,
    since they are explicitly and specifically suggested for this
    particular domain object (unlike every prior metadata module,
    where no such domain-specific fields were ever suggested) and a
    top-level organizational unit genuinely benefits from both. Field
    order: `created_at`, `version`, `correlation_id` (the established
    quartet's own relative order, unchanged), then `owner`, `tags`
    (the new, domain-specific fields, in the order this package's own
    suggested list gives them), then `extra` (last, per every prior
    convention without exception).

owner/tags Are System-Managed Fields, Not Builder-Overridable - See
builder.py:
    Mirrors TaskMetadata's own "created_at/version/correlation_id are
    system-assigned; only extra is caller-populated" precedent,
    extended to genuinely cover `owner`/`tags` as well:
    ProjectBuilder's own Responsibilities list names exactly "assign
    name, assign description, assign status, assign metadata" - one
    bullet for "assign metadata," not separate bullets for "assign
    owner"/"assign tags." Consistent with this codebase's own strict
    "no with_<field>() unless explicitly named" precedent
    (RelationshipBuilder/031, ExecutionResultBuilder/032,
    CapabilityExecutionResultBuilder/034, CapabilityContextBuilder/035),
    `owner` and `tags` join `created_at`/`version`/`correlation_id` as
    fields ProjectBuilder does not expose a dedicated setter for -
    they remain at their own defaults (`None`, an empty tuple) for
    every Project built via the supported ProjectBuilder path in
    Version 1, settable only through `with_metadata()`'s own `extra`
    mapping or by constructing ProjectMetadata directly. See builder.py's
    own module docstring for the complete reasoning, and this
    package's own Known Limitations for the fuller statement.

Mirrors ContextMetadata/PlanningMetadata/TraceMetadata/TaskMetadata/
RelationshipMetadata/ExecutionMetadata/CapabilityMetadata/
CapabilityExecutionMetadata/CapabilityContextMetadata's Shape For
Its Own Shared Fields:
    `created_at`, `version`, `correlation_id`, and `extra` are typed
    and defaulted identically to every sibling metadata module -
    `created_at` defaults to the current UTC time, `version` defaults
    to this module's own `PROJECT_METADATA_VERSION`, `correlation_id`
    defaults to a fresh uuid4 string, and `extra` is wrapped in
    `MappingProxyType` with a defensive copy in `__post_init__`,
    exactly as every prior metadata module already does.

tags Is Wrapped In A Tuple, Mirroring Every Ordered-Collection
Field's Own Convention:
    `tags` defaults to an empty tuple and is coerced to a tuple in
    `__post_init__` regardless of what sequence type is given,
    mirroring `Task.relationships` (031)/`Plan.tasks` (030)'s own
    "always stored as a tuple" convention for ordered collection
    fields.

Responsibilities:
    - ProjectMetadata: hold a Project's own creation timestamp,
      schema version, correlation identifier, owner, tags, and any
      caller-supplied extra data as an immutable value object.

Non-Responsibilities:
    - ProjectMetadata performs no computation and holds no runtime
      state - not a snapshot of any live service, not a cache.
    - ProjectMetadata performs no validation of its own fields beyond
      the standard `extra`/`tags` wrapping in `__post_init__` - see
      builder.py's own module docstring for where malformed input to
      the *builder's* own `with_metadata()` is rejected.

Dependencies:
    None beyond the standard library.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping, Optional, Sequence

PROJECT_METADATA_VERSION = "1.0"


@dataclass(frozen=True)
class ProjectMetadata:
    """
    Immutable, descriptive bookkeeping about a single Project. See the
    module docstring for the full field semantics and for why this
    module's own field set diverges from - while still following -
    every prior metadata module's own established convention.

    Fields:
        created_at: When this ProjectMetadata (and, in practice, the
            Project it describes) was created. Defaults to the
            current UTC time.
        version: The schema version of this metadata shape. Defaults
            to PROJECT_METADATA_VERSION.
        correlation_id: An opaque identifier for tracing this
            Project's own metadata across the system. Defaults to a
            fresh uuid4 string.
        owner: A human-readable identifier for who owns this Project.
            Defaults to None. Not settable via ProjectBuilder in
            Version 1 - see the module docstring.
        tags: Free-form labels organizing this Project. Defaults to
            an empty tuple. Always stored as a tuple, regardless of
            what sequence type is given. Not settable via
            ProjectBuilder in Version 1 - see the module docstring.
        extra: Caller-supplied key/value data, populated exclusively
            through ProjectBuilder.with_metadata(). Defaults to an
            empty mapping, wrapped in MappingProxyType.
    """

    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    version: str = PROJECT_METADATA_VERSION
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    owner: Optional[str] = None
    tags: Sequence[str] = field(default_factory=tuple)
    extra: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "tags", tuple(self.tags))
        object.__setattr__(self, "extra", MappingProxyType(dict(self.extra)))
