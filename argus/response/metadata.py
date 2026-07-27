"""
The ResponseMetadata value object for the ArgusOS Response Engine.

Purpose:
    Hold lightweight, descriptive bookkeeping about a single Response
    instance itself - when it was constructed, what response schema
    version produced it, a correlation identifier for tracing it, and
    any additional metadata carried through from the originating Plan
    - per factory/packages/027_RESPONSE_ENGINE.md. "Mirror the style
    used throughout ContextMetadata and PlanningMetadata."
    ResponseMetadata is pure data: it does not compute, validate its
    own timestamp against a clock at read time, or know anything
    about the Response it describes.

Mirrors ContextMetadata/PlanningMetadata's Shape, With One Named Field
Deviation:
    `argus.context.metadata.ContextMetadata` (Package 022) and
    `argus.planning.metadata.PlanningMetadata` (Package 023) both hold
    three system-assigned named fields (a creation timestamp, a schema
    version, a correlation identifier) plus one open `extra` mapping
    for genuinely arbitrary caller-supplied data - this module copies
    that exact shape. The one deviation: this package's own work order
    explicitly names the timestamp field `timestamp`
    ("Include: timestamp, version, correlation_id"), not `created_at`
    - both prior modules' own field name. Every other aspect of the
    shape (defaults, the `extra` mapping, the module-level `_VERSION`
    constant, the MappingProxyType wrapping) is copied unchanged; only
    this one field's name is deliberately different, per the work
    order's own explicit spelling, and is called out here rather than
    silently normalized to match the two precedents it otherwise
    mirrors exactly.

`extra` Carries The Plan's Own Metadata Forward:
    ResponseEngine "may depend only on: Plan" - it has no access to
    whatever metadata an AgentRequest/PipelineRequest originally
    carried (that chain terminates at PipelineResult.metadata, per
    Package 025's own design). The one metadata source ResponseEngine
    can legitimately read is the Plan it was given directly -
    `Plan.metadata`, which already carries `planning_session_id`,
    `cognitive_context_id`, and `constraints` forward from
    `Planner.plan_session()` (Package 024). `ResponseEngine.build_response()`
    copies `plan.metadata` into this field's `extra` mapping unchanged
    - see engine.py's own module docstring for the exact mechanism.

Responsibilities:
    - ResponseMetadata: hold a Response's own construction timestamp,
      schema version, correlation identifier, and metadata carried
      forward from the originating Plan as an immutable value object.

Non-Responsibilities:
    - ResponseMetadata performs no computation and holds no runtime
      state - not a snapshot of any live service, not a cache, and
      not a reference back to the Response it describes.
    - This module has no dependency on any other argus.response
      module, matching the "pure, dependency-free leaf" precedent set
      by every other value object in this codebase.

Dependencies:
    None.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping

#: The Response schema version this module produces. Not related to
#: CORE_SERVICES_VERSION (argus/bootstrap.py) - this versions the
#: shape of ResponseMetadata/Response itself, in case a future package
#: needs to distinguish responses produced by different schema
#: revisions. Mirrors argus.context.metadata.CONTEXT_METADATA_VERSION's
#: and argus.planning.metadata.PLANNING_METADATA_VERSION's identical
#: role.
RESPONSE_METADATA_VERSION = "1.0"


@dataclass(frozen=True)
class ResponseMetadata:
    """
    Immutable, lightweight bookkeeping about a single Response
    instance. See the module docstring for the full field semantics.

    Fields:
        timestamp: The UTC timestamp this ResponseMetadata was
            constructed. Defaults to the current time. Named
            `timestamp`, not `created_at`, per this package's own
            explicit work order - see the module docstring's "One
            Named Field Deviation" note.
        version: The Response schema version that produced this
            metadata. Defaults to RESPONSE_METADATA_VERSION.
        correlation_id: An identifier for tracing the owning Response.
            Defaults to a fresh uuid4 string.
        extra: Metadata carried forward from the originating Plan (see
            the module docstring's "extra Carries The Plan's Own
            Metadata Forward" note), plus any additional caller-
            supplied data. Defaults to an empty mapping.
    """

    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    version: str = RESPONSE_METADATA_VERSION
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    extra: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "extra", MappingProxyType(dict(self.extra)))
