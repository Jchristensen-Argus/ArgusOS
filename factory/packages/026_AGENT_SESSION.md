# Implementation Package 026 - Agent Session

## Objective

Implement the first-generation Agent Session. "An Agent Session
represents an ongoing interaction between a user and Argus. It owns
conversation continuity. It orchestrates the Cognitive Pipeline. It
does not perform reasoning. It does not perform planning. It does not
perform execution." This is the second new runtime service since
Package 021 - Package 025's Cognitive Pipeline was the first, and
Agent Session sits directly on top of it.

---

## Architectural Motivation

Prior to this package, the only way to run one full pass through the
cognitive architecture was to construct a `PipelineRequest` directly
and call `CognitivePipeline.run()`. Nothing represented the *user's*
side of that interaction - an identity for "this particular ongoing
conversation with this particular user," independent of any one
`PipelineRequest`/`PipelineResult` pair. `AgentSession` fills that
gap: it is the thing that persists across many `AgentService.run()`
calls (in a future package that actually stores and re-fetches one -
see Known Limitations), while `PipelineRequest`/`PipelineResult`
remain scoped to a single orchestration pass, exactly as they were
designed to be in Package 025.

---

## Architectural Position

```
User
    -> Agent Session
    -> Pipeline
    -> Conversation -> Memory -> Knowledge -> Reasoning -> Context
    -> Planning Session
    -> Planner
    -> Validated Plan
```

Agent Session sits above the Cognitive Pipeline, as the entry point a
user-facing caller uses instead of constructing a `PipelineRequest`
directly. It is orchestration only - no step in the pre-existing chain
gains new behavior because this package exists.

---

## New Package

```
argus/agent/
    __init__.py
    session.py
    request.py
    response.py
    interfaces.py
    exceptions.py
    service.py       (see "File Naming Deviation" below)
```

### File Naming Deviation

This package's own work order lists exactly six files for
`argus/agent/`, with no file named for `AgentService`'s own concrete
implementation - unlike Package 025's own listing, which named
`pipeline.py` explicitly alongside `request.py`/`result.py`/
`interfaces.py`/`exceptions.py` for exactly that purpose. Two shapes
were on the table: put the concrete `AgentService` inside
`interfaces.py` alongside `IAgentService` (matching the work order's
literal file count exactly), or add one additional file, `service.py`,
not named in the work order. Checked this codebase's own precedent
directly rather than guessing: every `interfaces.py` in this
repository - `argus/pipeline/`, `argus/planner/`, `argus/decision/`,
`argus/reasoning/`, `argus/memory_integration/`,
`argus/knowledge_graph/`, `argus/connectors/`, `argus/runtime/`,
`argus/context/`, `argus/planning/` - holds an ABC only, without a
single exception across eleven prior packages. Chose `service.py`,
preserving that unbroken rule at the cost of one small, explicitly
documented file addition. Flagged here, in `argus/agent/service.py`'s
own module docstring, and in `DEVLOG.md`, per the standing "flag
genuine ambiguities rather than guess silently" instruction.

---

## AgentSession

Immutable. Fields: `conversation` (required - `ConversationSession`),
`session_id` (defaulted, uuid4), `metadata` (defaulted, wrapped in
`MappingProxyType`). "The session owns one Conversation instance. The
Conversation remains the authoritative conversation model." Field
order in `session.py` places `conversation` first (it has no default)
ahead of `session_id`/`metadata` (both defaulted) - the same
listed-order-vs-declared-order deviation applied throughout this
codebase whenever a required field is listed after an optional one.

## AgentRequest

Immutable. Fields: `session` (required - `AgentSession`), `conversation`
(required - `ConversationSession`, a sibling field, never derived from
or cross-validated against `session.conversation`), `request_id`
(defaulted, uuid4), `metadata` (defaulted). "The request references an
AgentSession." Both `session` and `conversation` are placed before the
two defaulted fields in actual declaration order, for the same
field-ordering reason as `AgentSession`.

## AgentResponse

Immutable. Fields: `session` (required - `AgentSession`),
`pipeline_result` (required - `PipelineResult`), `response_id`
(defaulted, uuid4), `metadata` (defaulted). "Do not generate
natural-language responses. Do not perform execution. Wrap the
PipelineResult only." Verified directly in
`tests/test_agent_response.py`'s
`test_no_natural_language_or_execution_fields_exist`, which asserts
the dataclass's own field set is exactly these four names, nothing
more.

---

## Session Lifecycle

An `AgentSession` itself has no lifecycle of its own - it is a plain,
immutable value object, exactly like `PipelineRequest`/`PipelineResult`
(Package 025). "Lifecycle," in this package's Testing section, refers
to `AgentService`'s own `IService` lifecycle (`CREATED` ->
`INITIALIZING` -> `RUNNING` -> `STOPPING` -> `STOPPED`), not to any
state `AgentSession` itself transitions through. A single
`AgentSession` may be passed to many separate `AgentRequest`/
`AgentService.run()` calls over time (each producing its own
independent `AgentResponse`) - Version 1 does not store or re-fetch
sessions itself; see Known Limitations.

---

## Interaction Sequence

`AgentService.run(request)` performs exactly four steps, in order, and
nothing else:

```
1. Accept the AgentRequest              (validate its shape)
2. Build a PipelineRequest              (conversation=request.conversation,
                                          metadata=propagated)
3. Invoke cognitive_pipeline.run()      (delegates entirely to the
                                          existing Cognitive Pipeline)
4. Return an AgentResponse              (wraps the PipelineResult)
```

Step 2 propagates every key in `request.metadata`, plus
`agent_request_id` and `agent_session_id`, into the built
`PipelineRequest.metadata` - which `CognitivePipeline.run()` then
propagates further on its own, exactly as Package 025 already
established. Step 3 is the service's only genuine collaboration with a
live service; any exception it raises is re-wrapped as
`AgentExecutionError` (`raise ... from error`), the same "wrap a
delegate's own exception" shape `PipelineExecutionError` (Package 025)
established one layer below.

---

## Dependency Graph

```
AgentService
    depends on: ICognitivePipeline   (constructor-injected, genuinely called every run())

    does NOT depend on: IEventBus    (nothing of its own to publish)
    does NOT depend on: IPlanner, IReasoningEngine, IDecisionEngine,
                         any builder, any bootstrap internal
```

Per the explicit Dependency Rules: "AgentService may depend on:
ICognitivePipeline. AgentService shall not depend on: Planner,
Reasoning Engine, Decision Engine, Builders, Bootstrap internals. All
cognition flows through the Pipeline." All satisfied: the only
constructor dependency `AgentService.__init__()` accepts is
`cognitive_pipeline: ICognitivePipeline`; nothing else is imported or
held.

---

## Why No IEventBus

"No event publication" is explicit in this package's own AgentService
Responsibilities. `AgentService` has nothing of its own to publish -
the one event any given interaction might eventually cause
(`PLAN_CREATED`, `PLAN_UPDATED`) still fires from inside
`Planner.plan_session()`'s own pre-existing delegated calls, two
layers below `AgentService` itself. This is the second consecutive
new-service package (after `CognitivePipeline`, Package 025) with no
`IEventBus` dependency at all.

---

## Bootstrap Integration

Registered as the twenty-third core service and thirteenth `IService`
adopter. Constructed immediately after `cognitive_pipeline`, depending
on `cognitive_pipeline` alone - already constructed earlier in the
startup sequence, satisfying the explicit "Planner -> Pipeline ->
Agent Service" dependency order by placement. Startup Sequence gained
a new step 24 ("Construct the Agent Service"); the prior steps 24
("Register the... core services") and 25 ("Construct and start the
Application") renumbered to 25 and 26.
`_register_core_services()` gained an `agent_service: IAgentService`
parameter and the twenty-third entry
(`("agent_service", agent_service, IAgentService)`) in its
`core_services` tuple. Bootstrap itself never calls
`initialize()`/`start()` on `agent_service`, exactly as it never does
for any other core service.

---

## IService Adoption

`IAgentService` inherits `IService`, per explicit instruction -
"Register AgentService as the next core service," read the same way
`ICognitivePipeline`'s own instruction was read in Package 025.
Applying ADR-0002's criterion independently to `run()`, however, would
have suggested adoption on its own too: `run()` performs genuinely
effectful, single-step delegation to a live `CognitivePipeline` -
architecturally the same shape that made `CognitivePipeline.run()`
itself gated one layer below. `run()` is therefore gated: it raises
`AgentError` unless `status()` is `RUNNING`. This makes `AgentService`
the **third** IService adopter in this codebase, after Memory
Integration (Package 019) and the Cognitive Pipeline (Package 025),
where explicit instruction-to-adopt and ADR-0002's criterion applied
independently converge on the same answer.
`design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md` gained a new
Empirical Finding (Package 026) recording this, bringing the running
tally to an even three divergent, three convergent across six
directed-adoption data points - the first point in this ADR's history
where the two shapes are exactly balanced.

---

## Events

No new `EventType` members. `run()` never calls `self._publish()` or
holds an `IEventBus` reference at all - see "Why No IEventBus" above.
Every event this package's orchestration produces still fires from
inside `Planner.plan_session()`'s own pre-existing delegated calls,
two layers below `AgentService` itself.

---

## Repository Verification Note

The uploaded repository ("ArgusOS (25).zip") was verified against
this package's own general "verify repository state, verify version
consistency, verify HEAD/tag ancestry, run smoke validation"
pre-flight instruction. Findings: HEAD (`7c3da24`, "Synchronize
repository version with v0.2.5 release") is a clean, single-commit
descendant of tag `v0.2.5` (which points to `8382033`, "Implement
Package 025 Cognitive Pipeline"); `v0.2.4` also confirmed an ancestor
of HEAD via `git merge-base --is-ancestor`. `git diff v0.2.5..HEAD
--stat` shows exactly the expected one-line version-sync commit
(`argus/bootstrap.py`, 1 insertion, 1 deletion) - no anomaly.
`python -m pytest` passing (1486 passed, 38 subtests); `python -m
unittest discover -s tests` passing (1398); `python -m unittest
discover -s argus/tests` passing (64); `python main.py` starting and
shutting down cleanly (exit 0); `CORE_SERVICES_VERSION == "0.2.5"`
matching tag `v0.2.5`. All confirmed before any Package 026 code was
written.

---

## Files Created

```
argus/agent/__init__.py
argus/agent/session.py
argus/agent/request.py
argus/agent/response.py
argus/agent/interfaces.py
argus/agent/exceptions.py
argus/agent/service.py
factory/packages/026_AGENT_SESSION.md
tests/test_agent_session.py
tests/test_agent_request.py
tests/test_agent_response.py
tests/test_agent_service.py
```

## Files Modified

```
argus/bootstrap.py             (registered AgentService as the 23rd
                                 core service; new Startup Sequence
                                 step 24; renumbered old steps 24/25
                                 to 25/26)
tests/test_bootstrap.py        (CORE_SERVICE_NAMES synced; 3 new
                                 tests: registration, not-started,
                                 end-to-end orchestration)
argus/tests/test_bootstrap.py  (CORE_SERVICE_NAMES synced only, per
                                 the standing Package 011 rule)
design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md
                                (new Empirical Finding, Package 026)
CHANGELOG.md, DEVLOG.md, IMPLEMENTATION_REPORT.md, factory/ROADMAP.md
```

No other file was modified. Per this package's own explicit
Runtime/Planner/Pipeline/Conversation "No changes" instructions and
its Constraints section, `argus/runtime/`, `argus/planner/`,
`argus/pipeline/`, `argus/decision/`, `argus/reasoning/`,
`argus/context/`, `argus/planning/`, `argus/conversation/`, and
`argus/events/event_types.py` were left completely untouched -
confirmed via `git diff --stat` showing zero lines changed in any of
them.

---

## Test Results

New agent suites:
```
python -m pytest tests/test_agent_session.py tests/test_agent_request.py tests/test_agent_response.py tests/test_agent_service.py -q
71 passed in 0.05s
```

Canonical suite (`tests/`):
```
python -m unittest discover -s tests
Ran 1472 tests in 0.121s
OK
```

Per this package's explicit testing instruction:
```
python -m pytest
1560 passed, 38 subtests passed in 1.00s
```

The duplicate `argus/tests/` also verified passing standalone:
```
python -m unittest discover -s argus/tests -p "test_*.py"
Ran 64 tests in 0.015s
OK
```

`pyflakes` on every new/modified module: clean, no warnings (one
unused-import warning found and corrected during this package's own
verification pass - see Known Limitations / DEVLOG.md).

`python main.py`:
```
[INFO] argus: ArgusOS application started.
[INFO] argus: ArgusOS application shutting down.
```
Exit code 0.

---

## Coverage

Measured with `coverage.py`, `python -m coverage run -m pytest
tests/test_agent_session.py tests/test_agent_request.py
tests/test_agent_response.py tests/test_agent_service.py
tests/test_bootstrap.py`, reported with `--include="argus/agent/*"`:

```
argus/agent/__init__.py         7      0   100%
argus/agent/exceptions.py       3      0   100%
argus/agent/interfaces.py       7      0   100%
argus/agent/request.py         14      0   100%
argus/agent/response.py        14      0   100%
argus/agent/service.py         49      0   100%
argus/agent/session.py         12      0   100%
TOTAL                          106      0   100%
```

100% coverage across the entire `argus/agent/` package, reached on the
first measurement - no post-hoc gap-closing needed, unlike Package
025, whose own coverage required one corrective test.

---

## Version 1 Limitations

- **`AgentResponse` wraps the `PipelineResult` only** - no
  natural-language response is generated anywhere in this package; a
  caller wanting one must build it from `pipeline_result` themselves,
  in a future package explicitly scoped to do so.
- **`AgentRequest.conversation` is never cross-validated against
  `request.session.conversation`** - the two are independent fields,
  matching this codebase's own "no validation beyond isinstance
  checks" restraint elsewhere.
- **`AgentService` holds no `IEventBus` reference** - by design; it
  has nothing of its own to publish.
- **`AgentSession` is not persisted or re-fetched anywhere** - Version
  1 has no store; a caller constructs an `AgentSession` fresh (or
  holds one in memory across several `run()` calls) but nothing in
  this package saves one to disk or looks one up by `session_id`.
- **No AI, no LLM integration, no execution, no optimization, no
  persistence, no concurrency** - unchanged from every prior package
  in this phase.
- **The Agent Session is not yet invoked automatically by anything** -
  available to any caller holding an `AgentRequest`, but no automatic
  trigger (a Connector, a Scheduler tick, or similar) exists yet.
- The repository's stray `argus/` duplicate tree and legacy
  pre-Factory files remain unresolved, out of scope per the Founder's
  explicit repository rules.

---

## Future Expansion

- Introduce a session store (in-memory first, matching this
  codebase's own "Version 1 is always in-memory" pattern) so a
  `session_id` can be used to re-fetch an existing `AgentSession`
  across separate `run()` calls, rather than requiring the caller to
  hold the `AgentSession` object itself.
- Wire an automatic trigger (a Connector, a Scheduler tick, or
  similar) to call `AgentService.run()` on incoming external input,
  once a future package's work order explicitly asks for that
  integration.
- Consider whether a future package should add a natural-language
  response field to `AgentResponse` (or a sibling type) once AI/LLM
  integration is explicitly authorized - Version 1 deliberately wraps
  the `PipelineResult` only.
- Consider whether `AgentRequest` should eventually gain its own
  validation cross-checking `conversation` against
  `session.conversation`, if a future package finds allowing them to
  diverge silently to be a source of bugs rather than a useful
  flexibility.

---

## Release Rules

Per the Founder's explicit instruction: no commit, tag, or push was
performed. `CORE_SERVICES_VERSION` was not changed by this package -
it remains `"0.2.5"`. This package is not reported as complete or
released - implementation ends after successful local verification;
final validation, integration, release, version update, commit, and
tag are the Founder's responsibility against the live repository.
