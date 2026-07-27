"""
The Response value object for the ArgusOS Response Engine.

Purpose:
    Represent a single, immutable, standardized snapshot of one
    completed cognitive result - the validated Plan it wraps, that
    Plan's own planning status, an identity, and descriptive metadata
    - per factory/packages/027_RESPONSE_ENGINE.md. "The Response
    Engine converts a validated Plan into a structured response
    object... Its responsibility is to transform cognitive output into
    a standardized response contract." A Response is pure data: it
    does not generate AI text, does not execute the Plan it wraps, and
    does not communicate with any user interface.

No Natural-Language Text, No Markdown, No Rendering:
    "Do not include natural-language text. Do not include markdown.
    Do not include rendering. The Response object represents a
    completed cognitive result only." Response introduces no field
    describing "what Argus said" - the same restraint AgentResponse
    (Package 026) already showed toward `pipeline_result`/`response`;
    a caller wanting natural language must build it from `plan`
    themselves, in a future package explicitly scoped to do so (see
    factory/packages/027_RESPONSE_ENGINE.md's own Future AI
    Integration section).

`status` Is Copied From `plan.status`, Not Derived Here:
    `status` is a plain field, not a property computed from `plan` at
    read time - like every other value object in this codebase,
    Response performs no computation of its own (see "No Validation
    Here" below). `ResponseEngine.build_response()` is what actually
    copies `plan.status` into this field at construction time; holding
    both `plan` (the full object) and `status` (a copy of one of its
    own fields) is a deliberate, literal reading of this package's own
    explicit four-field list, not an oversight - the same kind of
    explicit-field-even-where-it-overlaps choice `PlanningSession`
    (Package 023) already made by holding a live `CognitiveContext`
    directly rather than only a derived identifier.

Both `plan` And `status` Are Required:
    Mirrors `PipelineResult`'s (Package 025) own "every field is
    required - this is always a complete snapshot" reasoning: a
    Response with no Plan it wraps is not a meaningful response to
    anything. `plan` has no default; only `response_id` (a fresh
    uuid4), `status` (defaults to the same `PlanStatus.CREATED`
    default `Plan.status` itself uses, for constructibility, though
    `ResponseEngine.build_response()` always supplies the Plan's own
    actual status explicitly), and `metadata` (a fresh
    `ResponseMetadata`) do.

Field Ordering Deviates From The Work Order's Own Listed Order:
    The work order lists Response's fields as `response_id`, `plan`,
    `status`, `metadata` - but `plan` has no default while
    `response_id` does (a fresh uuid4). Python dataclass field
    ordering requires every non-default field to precede every
    defaulted field, so `plan` is declared first in the actual code
    below - the same listed-order-vs-declared-order deviation already
    applied to `Entity`, `ReasoningQuery`, `DecisionRule`,
    `PipelineRequest`, `PipelineResult`, `AgentSession`, and
    `AgentRequest` whenever an identical tension arose.

No Validation Here - See engine.py:
    Like every other value object in this codebase, Response performs
    no validation of its own fields in __post_init__ beyond the
    standard `metadata` typing (a `ResponseMetadata`, not a bare
    mapping - see metadata.py). `ResponseEngine.build_response()` is
    the only component that constructs a Response during normal
    operation - see engine.py's own module docstring for the full
    construction sequence that produces one.

Responsibilities:
    - Response: hold the wrapped Plan, that Plan's own planning
      status, an identity, and descriptive ResponseMetadata as an
      immutable value object.

Non-Responsibilities:
    - Response performs no reasoning, decision making, planning, or
      execution of any kind - see this package's own Objective and
      Constraints.
    - This module depends only on argus.planner.plan (Plan,
      PlanStatus) and argus.response.metadata (ResponseMetadata) to
      type its own fields - it has no dependency on
      argus.response.engine, matching the "pure, dependency-free leaf"
      precedent set by every other value object in this codebase.

Dependencies:
    argus.planner.plan (Plan, PlanStatus), argus.response.metadata
    (ResponseMetadata).
"""

import uuid
from dataclasses import dataclass, field

from argus.planner.plan import Plan, PlanStatus
from argus.response.metadata import ResponseMetadata


@dataclass(frozen=True)
class Response:
    """
    An immutable, standardized snapshot of one completed cognitive
    result. See the module docstring for the full field semantics.

    Fields:
        plan: The validated Plan this Response wraps. Required.
        response_id: Unique identifier for this Response. Defaults to
            a fresh uuid4 string.
        status: The wrapped Plan's own planning status at the moment
            this Response was constructed. Defaults to
            PlanStatus.CREATED - see the module docstring's "status Is
            Copied From plan.status" note for why
            ResponseEngine.build_response() always supplies this
            explicitly rather than relying on the default.
        metadata: Descriptive bookkeeping about this Response,
            including metadata carried forward from `plan.metadata` -
            see metadata.py's own module docstring. Defaults to a
            fresh ResponseMetadata.
    """

    plan: Plan
    response_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: PlanStatus = PlanStatus.CREATED
    metadata: ResponseMetadata = field(default_factory=ResponseMetadata)
