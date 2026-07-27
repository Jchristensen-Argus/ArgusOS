"""
The Response value object for the ArgusOS Response Engine.

Purpose:
    Represent a single, immutable, standardized snapshot of one
    completed cognitive result - the validated Plan it wraps, the
    ExecutionResult recording how that Plan's own Tasks were
    processed, the ExecutionTrace recording how the request reached
    it, that Plan's own planning status, an identity, and descriptive
    metadata - per factory/packages/027_RESPONSE_ENGINE.md, as amended
    by factory/packages/028_EXECUTION_TRACE.md's own explicit
    "Response Integration" instruction and
    factory/packages/032_EXECUTION_ENGINE.md's own explicit "Response"
    instruction. "The Response Engine converts a validated Plan into a
    structured response object... Its responsibility is to transform
    cognitive output into a standardized response contract." A
    Response is pure data: it does not generate AI text, does not
    execute the Plan it wraps, and does not communicate with any user
    interface.

Package 032 Amendment - execution_result Joins plan/execution_trace:
    Package 028's own Response held five fields: `plan`,
    `execution_trace`, `response_id`, `status`, `metadata`. Package
    032's own explicit "Response" instruction is unambiguous: "Extend
    Response. Add: execution_result. Response now contains:
    response_id, plan, execution_result, execution_trace, status,
    metadata." `execution_result` is required, no-default, the same
    "every field required - this is always a complete snapshot"
    reasoning already applied to `plan` (027) and `execution_trace`
    (028) extends naturally to `execution_result`: a Response
    constructed without knowing how its own Plan's Tasks were
    processed is as incomplete as one constructed without the trace of
    how the request reached it. This is a genuinely additive change -
    every prior field is unchanged - but it is still a breaking change
    to direct `Response(...)` construction call sites (including this
    package's own pre-032 tests), since `execution_result` now has no
    default; see engine.py's own module docstring for how
    `ResponseEngine.build_response()`'s signature changed to supply
    it.

Package 028 Amendment - execution_trace Joins plan:
    Package 027's own Response held exactly four fields: `plan`,
    `response_id`, `status`, `metadata`. Package 028's own explicit
    "Response Integration" instruction is unambiguous: "extend
    Response. Add: execution_trace field. Response now contains:
    response_id, plan, execution_trace, status, metadata." `plan` and
    `execution_trace` are both required, no-default fields - the same
    "every field required - this is always a complete snapshot"
    reasoning already applied to `plan` alone in Package 027 (see
    below) extends naturally to `execution_trace`: a Response
    constructed without knowing how the request reached it is as
    incomplete as one constructed without the Plan itself. This is a
    genuinely additive change - every prior field is unchanged - but
    it is still a breaking change to direct `Response(...)`
    construction call sites (including this package's own pre-028
    tests), since `execution_trace` now has no default; see engine.py's
    own module docstring for how `ResponseEngine.build_response()`'s
    signature changed to supply it.

No Natural-Language Text, No Markdown, No Rendering:
    "Do not include natural-language text. Do not include markdown.
    Do not include rendering. The Response object represents a
    completed cognitive result only." Response introduces no field
    describing "what Argus said" - the same restraint AgentResponse
    (Package 026) already showed toward `pipeline_result`/`response`;
    a caller wanting natural language must build it from `plan`
    themselves, in a future package explicitly scoped to do so (see
    factory/packages/027_RESPONSE_ENGINE.md's own Future AI
    Integration section). `execution_trace` does not change this: per
    factory/packages/028_EXECUTION_TRACE.md, "the trace records that a
    stage occurred, not its internal reasoning" - it is exactly as
    free of natural language, rendering, and cognition as `plan`
    itself.

`status` Is Copied From `plan.status`, Not Derived Here:
    `status` is a plain field, not a property computed from `plan` at
    read time - like every other value object in this codebase,
    Response performs no computation of its own (see "No Validation
    Here" below). `ResponseEngine.build_response()` is what actually
    copies `plan.status` into this field at construction time; holding
    both `plan` (the full object) and `status` (a copy of one of its
    own fields) is a deliberate, literal reading of this package's own
    explicit field list, not an oversight - the same kind of
    explicit-field-even-where-it-overlaps choice `PlanningSession`
    (Package 023) already made by holding a live `CognitiveContext`
    directly rather than only a derived identifier.

`plan`, `execution_result`, And `execution_trace` Are All Required:
    Mirrors `PipelineResult`'s (Package 025) own "every field is
    required - this is always a complete snapshot" reasoning: a
    Response with no Plan it wraps, no record of how that Plan's own
    Tasks were processed, or no record of how it was reached, is not a
    meaningful response to anything. None of `plan`, `execution_result`,
    or `execution_trace` has a default; only `response_id` (a fresh
    uuid4), `status` (defaults to the same `PlanStatus.CREATED` default
    `Plan.status` itself uses, for constructibility, though
    `ResponseEngine.build_response()` always supplies the Plan's own
    actual status explicitly), and `metadata` (a fresh
    `ResponseMetadata`) do.

Field Ordering Deviates From The Work Order's Own Listed Order:
    Package 032's own work order lists Response's fields as
    `response_id`, `plan`, `execution_result`, `execution_trace`,
    `status`, `metadata` - but `plan`, `execution_result`, and
    `execution_trace` all have no default while `response_id` does (a
    fresh uuid4). Python dataclass field ordering requires every
    non-default field to precede every defaulted field, so `plan`,
    `execution_result`, and `execution_trace` are declared first in
    the actual code below, in the same relative order the work order
    lists them in - the same listed-order-vs-declared-order deviation
    already applied to `Entity`, `ReasoningQuery`, `DecisionRule`,
    `PipelineRequest`, `PipelineResult`, `AgentSession`,
    `AgentRequest`, and this same module's own `plan` field (027) and
    `execution_trace` field (028).

No Validation Here - See engine.py:
    Like every other value object in this codebase, Response performs
    no validation of its own fields in __post_init__ beyond the
    standard `metadata` typing (a `ResponseMetadata`, not a bare
    mapping - see metadata.py). `ResponseEngine.build_response()` is
    the only component that constructs a Response during normal
    operation - see engine.py's own module docstring for the full
    construction sequence that produces one, and argus.trace.builder's
    own module docstring for how the `ExecutionTrace` it receives is
    built.

Responsibilities:
    - Response: hold the wrapped Plan, the ExecutionResult recording
      how that Plan's own Tasks were processed, the ExecutionTrace
      recording how the request reached it, that Plan's own planning
      status, an identity, and descriptive ResponseMetadata as an
      immutable value object.

Non-Responsibilities:
    - Response performs no reasoning, decision making, planning, or
      execution of any kind - see this package's own Objective and
      Constraints.
    - This module depends only on argus.planner.plan (Plan,
      PlanStatus), argus.response.metadata (ResponseMetadata),
      argus.trace.trace (ExecutionTrace), and
      argus.execution_engine.result (ExecutionResult) to type its own
      fields - it has no dependency on argus.response.engine,
      argus.trace.builder, or argus.execution_engine.engine, matching
      the "pure, dependency-free leaf" precedent set by every other
      value object in this codebase.

Dependencies:
    argus.planner.plan (Plan, PlanStatus), argus.response.metadata
    (ResponseMetadata), argus.trace.trace (ExecutionTrace),
    argus.execution_engine.result (ExecutionResult) - Package 032.
"""

import uuid
from dataclasses import dataclass, field

from argus.execution_engine.result import ExecutionResult
from argus.planner.plan import Plan, PlanStatus
from argus.response.metadata import ResponseMetadata
from argus.trace.trace import ExecutionTrace


@dataclass(frozen=True)
class Response:
    """
    An immutable, standardized snapshot of one completed cognitive
    result. See the module docstring for the full field semantics.

    Fields:
        plan: The validated Plan this Response wraps. Required.
        execution_result: The ExecutionResult recording how this
            Plan's own Tasks were processed. Required - see the module
            docstring's "Package 032 Amendment" note.
        execution_trace: The ExecutionTrace recording how this request
            reached this Response. Required - see the module
            docstring's "Package 028 Amendment" note.
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
    execution_result: ExecutionResult
    execution_trace: ExecutionTrace
    response_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: PlanStatus = PlanStatus.CREATED
    metadata: ResponseMetadata = field(default_factory=ResponseMetadata)
