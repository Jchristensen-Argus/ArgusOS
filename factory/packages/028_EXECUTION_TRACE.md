# Implementation Package 028 - Execution Trace

## Objective

Implement the first-generation Execution Trace. "The Execution Trace
is an immutable record of how a request moved through Argus. It is
not logging. It is not debugging. It is not telemetry. It is a
first-class architectural object." Unlike every package since 024,
this one introduces no new runtime service - "No new core services.
TraceBuilder is not a service" - making it the first purely
infrastructure package since Planning Session (023).

---

## Architectural Motivation

Prior to this package, nothing in ArgusOS recorded that a request had
actually passed through `AgentService`, the `CognitivePipeline`, and
the `ResponseEngine` in that order - only the end result (a `Response`)
was ever visible. `ExecutionTrace` introduces a first-class,
independently inspectable record of *flow* - which components a
request touched, in what order, and when - deliberately without
recording *what any of them decided*. It is a companion object riding
alongside the request, not a replacement for logging, debugging, or
telemetry, all of which this package explicitly stays out of.

---

## Architectural Position

```
User
    -> Agent Service
    -> Execution Trace
    -> Pipeline
    -> Planner
    -> Response Engine
    -> Response
```

"The Execution Trace accompanies the request from beginning to end."
The trace begins inside `AgentService`, is threaded through as the
request proceeds, and is embedded in the final `Response` returned to
the caller - `Response.execution_trace`.

---

## New Package

```
argus/trace/
    __init__.py
    trace.py
    step.py
    metadata.py
    builder.py
    interfaces.py
    exceptions.py
```

---

## TraceStep

Immutable. Fields: `component` (required - a free-form string, e.g.
`"AgentService"`, `"CognitivePipeline"`, `"ResponseEngine"`), `action`
(required - a free-form string, e.g. `"entry"`, `"completed"`,
`"invoked"`), `step_id` (defaulted, uuid4), `timestamp` (defaulted,
current UTC time), `metadata` (defaulted, wrapped in
`MappingProxyType`). "Example component values: AgentService,
CognitivePipeline, Planner, ResponseEngine" - "Example," not a closed
enum, so `component`/`action` are plain `str` fields, not a
`TraceComponent`-style enum. "The trace records that a stage occurred,
not its internal reasoning" - `TraceStep` holds no reference to
whatever data the described component actually produced. Field order
in `step.py` places `component`/`action` first (neither has a
default) ahead of the three defaulted fields - the same
listed-order-vs-declared-order deviation applied throughout this
codebase whenever required fields are listed after optional ones.

## TraceMetadata

Immutable. Fields: `created_at` (defaulted, current UTC time),
`version` (defaulted, `TRACE_METADATA_VERSION`), `correlation_id`
(defaulted, uuid4), `extra` (defaulted, wrapped in
`MappingProxyType`). Unlike `ResponseMetadata`'s (Package 027) own
`timestamp` deviation, this package's own explicit field list spells
the timestamp field `created_at` - matching `ContextMetadata`/
`PlanningMetadata` exactly, with no naming deviation this time. `extra`
is not named in this package's own explicit field list either
(neither was it in Package 027's) - included anyway, for the same
reason both times: every sibling metadata class ends with one, and
`TraceBuilder.with_metadata()` needs somewhere to accumulate into.

## ExecutionTrace

Immutable. Fields: `trace_id` (defaulted, uuid4), `steps` (defaulted,
an empty tuple - always stored as a tuple regardless of the sequence
type given), `metadata` (defaulted, a fresh `TraceMetadata`). Every
field carries a default - `ExecutionTrace()` with no arguments is
always valid, representing a fresh, empty trace, matching this
package's own explicit "empty trace, populated trace" Testing
category.

---

## TraceBuilder

The one mutable object in this package - "The builder is the only
mutable object" - mirroring `ContextBuilder`/`PlanningSessionBuilder`'s
(022/023) own shape and validation discipline exactly.

- `with_step(component, action, *, metadata=None)` - validates both
  arguments are non-empty strings (raising `InvalidTraceStepError`
  otherwise), constructs a fresh immutable `TraceStep` with its own
  `step_id` and a timestamp captured at the moment of the call,
  appends it, and returns `self`. Every call accumulates, in order -
  there is no "singular field, overwritten" exception here, unlike
  `ContextBuilder.with_conversation()`/`PlanningSessionBuilder.
  with_context()`.
- `with_metadata(key, value)` - accumulates into the eventual
  `TraceMetadata.extra`, last-call-wins on repeated keys, the same
  rule `ContextBuilder`/`PlanningSessionBuilder`'s own `with_metadata()`
  already use.
- `build()` - returns an independent `ExecutionTrace` snapshot from
  the builder's current accumulated state. Callable more than once
  against the same builder without mutating an earlier snapshot -
  `ExecutionTrace.__post_init__()` copies the `steps` sequence it is
  given, the same "independent snapshot" guarantee `ContextBuilder`/
  `PlanningSessionBuilder`'s own `build()` already provide.
- `trace_id` is generated once, in `__init__` - not regenerated on
  every `build()` call - so repeated snapshots of the same builder
  (as more steps accumulate between them) all describe the same
  logical trace, sharing one identity.

`ITraceBuilder` does not inherit `IService` - "TraceBuilder is not a
service" - mirroring `ICognitiveContextBuilder`/
`IPlanningSessionBuilder`'s own identical choice; a builder has no
meaningful start/stop lifecycle, only a short, per-request existence.

---

## Interaction Flow

`AgentService.run()`'s own interaction sequence, amended by this
package, now reads:

```
1. Accept the AgentRequest
2. Build a PipelineRequest
3. Create a fresh TraceBuilder; record ("AgentService", "entry")        [NEW]
4. Invoke cognitive_pipeline.run()                    -> PipelineResult
5. Record ("CognitivePipeline", "completed"),
   record ("ResponseEngine", "invoked"),
   build() the finished ExecutionTrace                                  [NEW]
6. Invoke response_engine.build_response(plan, execution_trace) -> Response  [AMENDED]
7. Return an AgentResponse wrapping the Response
```

Steps 3 and 5 are new; step 6 is amended (a second parameter,
`execution_trace`); steps 1, 2, 4, and 7 are unchanged from Package
027.

### Engineering Decision - Reconciling The Integration Diagram With The Dependency Rule

This package's own Integration section's arrow diagram lists steps in
this literal order: create TraceBuilder -> record AgentService entry
-> Pipeline -> record Pipeline completion -> Response Engine -> record
Response completion -> build ExecutionTrace - "build ExecutionTrace"
listed dead last, after Response Engine has already been invoked. Read
with total literalness, this would mean the trace `ResponseEngine`
"receives" is not yet built at the moment it receives it - directly
conflicting with this same package's own Dependency Rule: "ResponseEngine
shall not construct traces. It receives the finished trace." A trace
cannot simultaneously be "finished" and "not yet built."

The Dependency Rule - phrased as "shall/shall not," this codebase's
strongest form of instruction - took precedence over the diagram's own
literal arrow ordering, read the way every prior package's own
"Architectural Position" diagram has been read throughout this
project: as a narrative summary of the stages involved, not a strict
line-by-line call sequence. Concretely: the step the diagram calls
"record Response completion" is recorded as `("ResponseEngine",
"invoked")`, immediately *before* `build_response()` is called, not
after - an honest description of what has actually occurred at the
moment it is recorded ("the trace records that a stage occurred, not
its internal reasoning" - labeling something "completed" before it has
completed would misrepresent what happened). This keeps the trace
genuinely finished and immutable at the exact moment `ResponseEngine`
receives it, honors the Dependency Rule literally, and still records
all three example component values this package's own `step.py`
names, in the finished trace `Response.execution_trace` ultimately
exposes.

Two alternative readings were considered and rejected: building the
trace twice and swapping a "more complete" one into the returned
`Response` via `dataclasses.replace()` after the fact (rejected - this
would have `AgentService` itself constructing/modifying `Response`
instances, a responsibility this codebase has never given anything but
`ResponseEngine`); and treating the diagram as strictly authoritative
and shipping the resulting contradiction unresolved (not actually an
option - the code has to do one specific thing).

---

## Dependency Graph

```
ExecutionTrace / TraceStep / TraceMetadata
    depend on: nothing but each other (immutable value objects)

TraceBuilder
    depends on: nothing at construction time

AgentService (amended)
    depends on: ICognitivePipeline   (unchanged, Package 026)
    depends on: IResponseEngine      (unchanged, Package 027)
    depends on: TraceBuilder         (new, this package - constructed
                                       directly inside run(), not
                                       injected via __init__())

ResponseEngine (amended)
    depends on: Plan             (unchanged, per-call argument)
    depends on: ExecutionTrace   (new, this package - per-call
                                   argument, never constructed)
```

Per the explicit Dependency Rules: "Execution Trace may depend only on
immutable value objects. AgentService may depend on: TraceBuilder.
ResponseEngine shall not construct traces. It receives the finished
trace." All satisfied: `TraceBuilder` is constructed fresh inside every
`run()` call rather than injected as a long-lived collaborator, since
it is a short-lived, per-request accumulator, not a service - `AgentService.
__init__()`'s own two-dependency shape (unchanged since Package 027)
is untouched by this package.

---

## Bootstrap Integration

None. "No new core services. TraceBuilder is not a service." `argus/
bootstrap.py` is completely untouched by this package - confirmed via
`git diff --stat -- argus/bootstrap.py` showing zero lines changed,
the first package since Planning Session (023) for which that is
true. `CORE_SERVICES_VERSION` remains `"0.2.7"`.

---

## IService Adoption

None. `ITraceBuilder` does not inherit `IService` - the same "not an
IService" shape Cognitive Context (022) and Planning Session (023)
already established for infrastructure packages that expand no
service registry. No new entry was added to `design/decisions/
0002_ISERVICE_ADOPTION_CRITERION.md`, matching the precedent already
set by those same two packages (neither of which added one either).

---

## Events

No new `EventType` members. Neither `TraceBuilder` nor any
`argus.trace` value object calls `self._publish()` or holds an
`IEventBus` reference - there is nothing in this package with a
collaborator to publish through in the first place.

---

## Repository Verification Note

The uploaded repository ("ArgusOS (27).zip") was verified against
this package's own general "verify repository state, verify version
consistency, verify HEAD/tag ancestry, run smoke validation"
pre-flight instruction. Findings: HEAD (`36b5226`, "Synchronize
repository version with v0.2.7 release") is a clean, single-commit
descendant of tag `v0.2.7` (which points to `4fc250f`, "Implement
Package 027 Response Engine"). `git diff v0.2.7..HEAD --stat` shows
exactly the expected one-line version-sync commit (`argus/bootstrap.py`,
1 insertion, 1 deletion) - no anomaly. `python -m pytest` passing
(1617 passed, 38 subtests); `python -m unittest discover -s tests`
passing (1529); `python -m unittest discover -s argus/tests` passing
(64); `python main.py` starting and shutting down cleanly (exit 0);
`CORE_SERVICES_VERSION == "0.2.7"` matching tag `v0.2.7`; `argus/
response/response.py`'s pre-Package-028 field list (`plan`,
`response_id`, `status`, `metadata` - no `execution_trace`) confirmed
via direct inspection. All confirmed before any Package 028 code was
written.

---

## Files Created

```
argus/trace/__init__.py
argus/trace/trace.py
argus/trace/step.py
argus/trace/metadata.py
argus/trace/builder.py
argus/trace/interfaces.py
argus/trace/exceptions.py
factory/packages/028_EXECUTION_TRACE.md
tests/test_trace.py
tests/test_trace_step.py
tests/test_trace_metadata.py
tests/test_trace_builder.py
```

## Files Modified

```
argus/response/response.py     (Response gained a required
                                 execution_trace: ExecutionTrace field,
                                 declared alongside plan ahead of the
                                 defaulted fields)
argus/response/interfaces.py   (IResponseEngine.build_response()
                                 gained a second required parameter,
                                 execution_trace: ExecutionTrace)
argus/response/engine.py       (ResponseEngine.build_response()
                                 amended to match; validates and
                                 embeds execution_trace unmodified)
argus/response/exceptions.py   (added InvalidExecutionTraceError)
argus/response/__init__.py     (re-exports InvalidExecutionTraceError)
argus/agent/service.py         (run() creates a fresh TraceBuilder,
                                 records three steps, and passes the
                                 finished ExecutionTrace to
                                 response_engine.build_response())
argus/agent/interfaces.py      (IAgentService.run()'s own docstring
                                 updated to describe trace construction;
                                 abstract method signature unchanged)
tests/test_response.py         (execution_trace field added throughout;
                                 new ExecutionTraceFieldTests)
tests/test_response_engine.py  (execution_trace parameter added
                                 throughout; new ValidExecutionTraceTests/
                                 InvalidExecutionTraceTests)
tests/test_agent_response.py   (_response() helper updated to supply
                                 an ExecutionTrace)
tests/test_agent_service.py    (RecordingResponseEngine/
                                 RaisingResponseEngine amended to the
                                 two-argument build_response() shape;
                                 new TraceInvocationTests)
tests/test_bootstrap.py        (response_engine ungated smoke test
                                 amended for the new signature; the
                                 Agent Service end-to-end test gained
                                 an execution_trace assertion)
CHANGELOG.md, DEVLOG.md, IMPLEMENTATION_REPORT.md, factory/ROADMAP.md
```

No other file was modified. Per this package's own explicit "Do not
modify: Planner, Reasoning, Decision, Memory, Knowledge" instruction
and "Runtime: No changes. Pipeline: No changes. Planner: No changes,"
`argus/bootstrap.py`, `argus/planner/`, `argus/planning/`, `argus/
context/`, `argus/conversation/`, `argus/memory/`, `argus/
memory_integration/`, `argus/knowledge/`, `argus/knowledge_graph/`,
`argus/decision/`, `argus/reasoning/`, `argus/pipeline/`,
`argus/tests/test_bootstrap.py`, and `argus/events/event_types.py`
were left completely untouched - confirmed via `git diff --stat`
showing zero lines changed in any of them.

---

## Test Results

New trace suites:
```
python -m pytest tests/test_trace.py tests/test_trace_step.py tests/test_trace_metadata.py tests/test_trace_builder.py -q
58 passed in 0.05s
```

Amended response/agent suites:
```
python -m pytest tests/test_response.py tests/test_response_engine.py tests/test_agent_response.py tests/test_agent_service.py tests/test_bootstrap.py -q
all passed
```

Canonical suite (`tests/`):
```
python -m unittest discover -s tests
Ran 1604 tests in 0.115s
OK
```

Per this package's explicit testing instruction:
```
python -m pytest
1692 passed, 38 subtests passed in 1.05s
```

The duplicate `argus/tests/` also verified passing standalone:
```
python -m unittest discover -s argus/tests -p "test_*.py"
Ran 64 tests in 0.014s
OK
```

`python main.py`:
```
[INFO] argus: ArgusOS application started.
[INFO] argus: ArgusOS application shutting down.
```
Exit code 0.

---

## Coverage

Measured with `coverage.py`, `python -m coverage run -m pytest`:

```
--include="argus/trace/*"
argus/trace/__init__.py       7      0   100%
argus/trace/builder.py       29      0   100%
argus/trace/exceptions.py     2      0   100%
argus/trace/interfaces.py    10      0   100%
argus/trace/metadata.py      14      0   100%
argus/trace/step.py          14      0   100%
argus/trace/trace.py         12      0   100%
TOTAL                        88      0   100%

--include="argus/response/*"
argus/response/__init__.py    6      0   100%
argus/response/engine.py     31      0   100%
argus/response/exceptions.py  3      0   100%
argus/response/interfaces.py  8      0   100%
argus/response/metadata.py   14      0   100%
argus/response/response.py   12      0   100%
TOTAL                        74      0   100%

--include="argus/agent/*"
argus/agent/__init__.py         7      0   100%
argus/agent/exceptions.py       3      0   100%
argus/agent/interfaces.py       7      0   100%
argus/agent/request.py         14      0   100%
argus/agent/response.py        14      0   100%
argus/agent/service.py         61      0   100%
argus/agent/session.py         12      0   100%
TOTAL                          118      0   100%
```

100% coverage across the entire `argus/trace/` package (new), and
100% remains across the entire `argus/response/` package (net +7
statements from Package 027's 67) and the entire `argus/agent/`
package (net +6 statements from Package 027's 112) - all reached on
the first measurement, no post-hoc gap-closing needed.

---

## Version 1 Limitations

- **`TraceStep.component`/`.action` are open strings** - not a closed
  enum, and validated only for "non-empty string," per this package's
  own "Example component values" phrasing rather than an exhaustive
  list.
- **Only three stages are recorded in Version 1** - `AgentService`
  entry, `CognitivePipeline` completion, `ResponseEngine` invocation.
  The trace does not reach inside the Pipeline to record `Planner`/
  `Reasoning`/`Decision` sub-stages individually, per this package's
  own explicit "Do not modify: Planner, Reasoning, Decision" constraint.
- **The `("ResponseEngine", "invoked")` step is recorded before, not
  after, `build_response()` actually returns** - see the "Engineering
  Decision" note above; the trace therefore never records whether the
  Response Engine call itself succeeded, only that it was about to be
  invoked with a fully-formed trace already in hand.
- **No persistence, no querying, no visualization** - each
  `ExecutionTrace` lives only as long as the `Response` object that
  holds it; nothing stores traces beyond that.
- **No AI, no optimization, no concurrency** - unchanged from every
  prior package in this phase.
- The repository's stray `argus/` duplicate tree and legacy
  pre-Factory files remain unresolved, out of scope per the Founder's
  explicit repository rules.

---

## Future AI Integration

- A future observability/debugging package may consume
  `Response.execution_trace` directly - it is already a stable,
  independently inspectable object, requiring no new API surface to
  read.
- A future package may extend the trace to record sub-stages inside
  the Cognitive Pipeline itself (Reasoning, Decision, Memory,
  Knowledge) - deliberately out of scope here, since this package's
  own explicit Integration section instructs "the trace begins inside
  AgentService" and "Do not modify: Planner, Reasoning, Decision,
  Memory, Knowledge."
- Any future persistence or querying layer for traces should treat
  `ExecutionTrace`/`TraceStep`/`TraceMetadata` as the stable schema to
  serialize - all three are already plain, immutable value objects
  with no behavior to strip out.

---

## Release Rules

Per the Founder's explicit instruction: no commit, tag, or push was
performed. `CORE_SERVICES_VERSION` was not changed by this package -
it remains `"0.2.7"`. This package is not reported as complete or
released - implementation ends after successful local verification;
final validation, integration, release, version update, commit, and
tag are the Founder's responsibility against the live repository.
