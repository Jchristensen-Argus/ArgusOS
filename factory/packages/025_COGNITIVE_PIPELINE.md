# Implementation Package 025 - Cognitive Pipeline

## Objective

Implement the first-generation Cognitive Pipeline. "The Cognitive
Pipeline orchestrates the existing cognitive architecture. It does
not introduce new reasoning. It does not introduce AI. It does not
change planner behavior. Its responsibility is orchestration only."
This is the first new runtime service since Package 021 - Packages
022-024 each extended the cognitive architecture (a transport object,
a second transport object, and a new Planner entry point,
respectively) without adding a core service of their own.

---

## Architectural Position

```
User Request -> Cognitive Pipeline -> Conversation -> Memory -> Knowledge
             -> Reasoning -> Context -> Planning Session -> Planner
             -> Validated Plan
```

The Pipeline sits above the entire pre-existing chain, as the single
new entry point a caller uses instead of manually sequencing
`ContextBuilder` -> `PlanningSessionBuilder` -> `Planner.plan_session()`
by hand. It is orchestration only - no step in that chain gains new
behavior because the Pipeline exists.

---

## New Package

```
argus/pipeline/
    __init__.py
    pipeline.py
    request.py
    result.py
    interfaces.py
    exceptions.py
```

---

## Responsibilities

`CognitivePipeline` shall: accept a `PipelineRequest`, orchestrate the
existing components (`ContextBuilder`, `PlanningSessionBuilder`,
`Planner`), and produce a `PipelineResult`.

`CognitivePipeline` shall NOT: implement reasoning, decision making,
or planning of its own; execute workflows; or own any persistence.
Every one of these is satisfied by construction, not by discipline -
the Pipeline has no code path that could do any of them. `run()`
contains exactly the six steps below and nothing else.

---

## PipelineRequest

Immutable. Fields: `request_id` (defaulted, uuid4), `conversation`
(required - `ConversationSession`), `metadata` (defaulted, wrapped in
`MappingProxyType`). "The request contains the existing Conversation
object. Do not introduce raw text processing here" - `conversation`
is accepted and passed through exactly as given; the Pipeline never
inspects, tokenizes, or otherwise processes its message content.
Field order in `request.py` places `conversation` first (it has no
default) ahead of `request_id`/`metadata` (both defaulted) - Python
dataclass field ordering requires non-default fields before defaulted
ones, the same reordering-from-the-work-order's-own-listed-order
pattern applied throughout this codebase whenever a required field is
listed after an optional one (`Entity`, `ReasoningQuery`,
`DecisionRule`, and now this).

## PipelineResult

Immutable. Fields: `pipeline_id` (defaulted, uuid4), `conversation`,
`cognitive_context`, `planning_session`, `plan` (all four required),
`metadata` (defaulted). "No execution results. No runtime state" -
verified directly in `tests/test_pipeline_result.py`'s
`test_no_execution_or_runtime_fields_exist`, which asserts the
dataclass's own field set is exactly these six names, nothing more.
The four required fields are placed before the two defaulted ones in
actual declaration order, for the same field-ordering reason as
`PipelineRequest`.

---

## Orchestration Sequence

`CognitivePipeline.run(request)` performs exactly these six steps, in
order, and nothing else:

```
1. Accept the PipelineRequest                 (validate its shape)
2. Obtain the Conversation                    (request.conversation - already the object)
3. Build a CognitiveContext                   (ContextBuilder().with_conversation(...).build())
4. Build a PlanningSession                    (PlanningSessionBuilder().with_context(...).build())
5. Invoke planner.plan_session()              (delegates entirely to the existing Planner)
6. Return a PipelineResult
```

Step 2 is a trivial extraction, not a lookup - the work order's own
PipelineRequest description already states "the request contains the
existing Conversation object," and the explicit Dependency Rules name
only `Planner`, `PlanningSession`, and `CognitiveContext` as things
the Pipeline may depend on; `IConversationManager` is absent from that
list, confirming no manager lookup is intended. Steps 3 and 4 use
`ContextBuilder`/`PlanningSessionBuilder` (Packages 022/023)
constructed fresh inside `run()` and discarded once `.build()`
returns - never stored as instance state, never accepted as
constructor parameters. Step 5 is the Pipeline's only genuine
collaboration with a live service; any exception it raises is
re-wrapped as `PipelineExecutionError` (`raise ... from error`), the
same "wrap a delegate's own exception" shape `RuleEvaluationError`
(Package 021) established.

---

## Dependency Graph

```
CognitivePipeline
    depends on: IPlanner            (constructor-injected, genuinely called every run())
    depends on: ContextBuilder      (constructed fresh inside run(), never held)
    depends on: PlanningSessionBuilder (constructed fresh inside run(), never held)

    does NOT depend on: IEventBus   (nothing of its own to publish)
    does NOT depend on: IConversationManager, IMemoryIntegration,
                         IKnowledgeGraph, IReasoningEngine,
                         IDecisionEngine, IAgentRuntime
```

Per the explicit Dependency Rules: "Pipeline may depend on: Planner,
PlanningSession, CognitiveContext. Pipeline shall not: depend on
builders outside of construction, perform direct event publication,
modify immutable objects." All three are satisfied: the only
long-lived dependency `CognitivePipeline.__init__()` accepts is
`planner: IPlanner`; both builders are local variables inside `run()`
alone; every object `run()` touches (`ConversationSession`,
`CognitiveContext`, `PlanningSession`, `Plan`) is already immutable,
so there is no mutation path to accidentally take.

---

## Why No IEventBus

"Pipeline shall not: perform direct event publication. No new
EventTypes. Reuse existing planner behavior" together mean the
Pipeline has nothing of its own to publish - `PLAN_CREATED` and
`PLAN_UPDATED` already fire from inside `Planner.plan_session()`'s own
pre-existing delegated `create_plan()`/`add_step()` calls. Holding an
unused `IEventBus` reference purely for structural consistency with
every other `IService` adopter in this codebase would have been
decorative, not functional, so it was omitted - `CognitivePipeline` is
the first `IService` adopter in this codebase with no `IEventBus`
dependency at all.

---

## Why No Goals Or Constraints In Version 1

The `PlanningSession` `CognitivePipeline` builds always has empty
`goals`/`constraints` tuples, because the Pipeline has zero dependency
on the Reasoning Engine or Decision Engine - it has no source to
populate either from. This is a direct, necessary consequence of "It
does not introduce new reasoning. It does not change planner
behavior": the `Plan` `Planner.plan_session()` returns is therefore
always zero-step in Version 1, exactly the same shape an empty
`PlanningSession` produces when built by hand.

---

## Bootstrap Integration

Registered as the twenty-second core service and twelfth `IService`
adopter. Constructed immediately after `connector_manager`, depending
on `planner` alone - already constructed earlier in the startup
sequence, satisfying "Planner must already exist before Pipeline" by
placement rather than by any explicit ordering check. Startup Sequence
gained a new step 23 ("Construct the Cognitive Pipeline"); the prior
steps 23 ("Register the... core services") and 24 ("Construct and
start the Application") renumbered to 24 and 25.
`_register_core_services()` gained a `cognitive_pipeline:
ICognitivePipeline` parameter and the twenty-second entry
(`("cognitive_pipeline", cognitive_pipeline, ICognitivePipeline)`) in
its `core_services` tuple. Bootstrap itself never calls
`initialize()`/`start()` on `cognitive_pipeline`, exactly as it never
does for any other core service - a caller must do that explicitly, as
`tests/test_bootstrap.py`'s new end-to-end test does.

---

## IService Adoption

`ICognitivePipeline` inherits `IService`, per explicit instruction -
"Register the Cognitive Pipeline as a core service." Applying
ADR-0002's criterion independently to `run()`, however, would have
suggested adoption on its own too: `run()` coordinates genuinely
effectful, multi-step orchestration across a live downstream service
(building two transport objects, then invoking `Planner`), the same
kind of "active work" that made `ConversationManager.receive()`
(Package 011), `AgentRuntime`'s pause/cancel surface (Package 016),
`ConnectorManager.invoke()` (Package 017), and `MemoryIntegration`'s
three methods (Package 019) genuinely gated - not the synchronous,
single-system lookups that left Packages 018, 020, and 021 zero-gated.
`run()` is therefore gated: it raises `PipelineError` unless
`status()` is `RUNNING`. This makes `CognitivePipeline` the **second**
IService adopter in this codebase, after Memory Integration (Package
019), where explicit instruction-to-adopt and ADR-0002's criterion
applied independently converge on the same answer, rather than
diverging as in Packages 018, 020, and 021.
`design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md` gained a new
Empirical Finding (Package 025) recording this, updating the running
tally to three divergent, two convergent across five directed-adoption
data points.

---

## Events

No new `EventType` members. `run()` never calls `self._publish()` or
holds an `IEventBus` reference at all - see "Why No IEventBus" above.
Every event this package's orchestration produces (`PLAN_CREATED`
once, `PLAN_UPDATED` once per goal - zero, in Version 1, since
`goals` is always empty) is published by `Planner.plan_session()`'s
own pre-existing delegated calls, exactly as it would be for any other
caller of that method.

---

## Repository Verification Note

The uploaded repository ("ArgusOS (24).zip") was verified against
this package's own general "verify repository state, verify version
consistency, verify HEAD/tag ancestry, run smoke validation"
pre-flight instruction. Findings: HEAD (`2458512`, "Synchronize
repository version with v0.2.4 release") is a clean, single-commit
descendant of tag `v0.2.4` (which points to `888f611`, "Implement
Package 024 Planner Session Integration"); `v0.2.3` also confirmed an
ancestor of HEAD via `git merge-base --is-ancestor`. `git diff
v0.2.4..HEAD --stat` shows exactly the expected one-line version-sync
commit (`argus/bootstrap.py`, 1 insertion, 1 deletion) - no anomaly.
`argus/planner/planner.py` confirmed to already contain
`def plan_session` (Package 024); `python -m pytest` passing (1428
passed, 38 subtests); `python -m unittest discover -s tests` passing
(1340); `python -m unittest discover -s argus/tests` passing (64);
`python main.py` starting and shutting down cleanly (exit 0);
`CORE_SERVICES_VERSION == "0.2.4"` matching tag `v0.2.4`. All confirmed
before any Package 025 code was written.

---

## Files Created

```
argus/pipeline/__init__.py
argus/pipeline/pipeline.py
argus/pipeline/request.py
argus/pipeline/result.py
argus/pipeline/interfaces.py
argus/pipeline/exceptions.py
factory/packages/025_COGNITIVE_PIPELINE.md
tests/test_pipeline.py
tests/test_pipeline_request.py
tests/test_pipeline_result.py
```

## Files Modified

```
argus/bootstrap.py             (registered CognitivePipeline as the
                                 22nd core service; new Startup
                                 Sequence step 23; renumbered old
                                 steps 23/24 to 24/25)
tests/test_bootstrap.py        (CORE_SERVICE_NAMES synced; 3 new
                                 tests: registration, not-started,
                                 end-to-end orchestration)
argus/tests/test_bootstrap.py  (CORE_SERVICE_NAMES synced only, per
                                 the standing Package 011 rule)
design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md
                                (new Empirical Finding, Package 025)
CHANGELOG.md, DEVLOG.md, IMPLEMENTATION_REPORT.md, factory/ROADMAP.md
```

No other file was modified. Per this package's own explicit
Bootstrap/Runtime/Planner/Decision Engine/Cognitive Context/Planning
Session "No changes" instructions, `argus/runtime/`,
`argus/decision/`, `argus/reasoning/`, `argus/context/`,
`argus/planning/`, `argus/planner/`, and
`argus/events/event_types.py` were left completely untouched -
confirmed via `git diff --stat` showing zero lines changed in any of
them.

---

## Test Results

New pipeline suites:
```
python -m pytest tests/test_pipeline.py tests/test_pipeline_request.py tests/test_pipeline_result.py -q
55 passed in 0.05s
```

Canonical suite (`tests/`):
```
python -m unittest discover -s tests
Ran 1398 tests in 0.111s
OK
```

Per this package's explicit testing instruction:
```
python -m pytest
1486 passed, 38 subtests passed in 0.94s
```

The duplicate `argus/tests/` also verified passing standalone:
```
python -m unittest discover -s argus/tests -p "test_*.py"
Ran 64 tests in 0.016s
OK
```

`pyflakes` on every new/modified module: clean, no warnings.

`python main.py`:
```
[INFO] argus: ArgusOS application started.
[INFO] argus: ArgusOS application shutting down.
```
Exit code 0.

---

## Coverage

Measured with `coverage.py`, `python -m coverage run -m pytest
tests/test_pipeline.py tests/test_pipeline_request.py
tests/test_pipeline_result.py tests/test_bootstrap.py`, reported with
`--include="argus/pipeline/*"`:

```
argus/pipeline/__init__.py         6      0   100%
argus/pipeline/exceptions.py       3      0   100%
argus/pipeline/interfaces.py       7      0   100%
argus/pipeline/pipeline.py        55      0   100%
argus/pipeline/request.py         12      0   100%
argus/pipeline/result.py          18      0   100%
TOTAL                             101      0   100%
```

100% coverage across the entire `argus/pipeline/` package, reached
after correcting one test (`run()`'s second `isinstance` check, on
`request.conversation`, was initially untested because the first
attempt at that test used a fabricated request class that failed the
*first* `isinstance` check before ever reaching the second - corrected
by constructing a real `PipelineRequest` with a bogus `conversation`
field instead, which `request.py`'s own "no validation here" design
makes entirely legal to do). Overall repository regression remains
green; `argus/bootstrap.py`'s own coverage was not separately
re-measured, since this package's coverage scope is `argus/pipeline/`
only, per the work order's own "100% coverage on all new modules."

---

## Known Limitations

- **The built `PlanningSession` always has empty `goals`/`constraints`
  in Version 1** - the Pipeline has no dependency on the Reasoning
  Engine or Decision Engine, so it has no source to populate either
  from; the resulting `Plan` is therefore always zero-step. See "Why
  No Goals Or Constraints In Version 1" above.
- **`CognitivePipeline` holds no `IEventBus` reference** - by design;
  it has nothing of its own to publish. See "Why No IEventBus" above.
- **No AI, no LLM integration, no optimization, no persistence, no
  concurrency** - unchanged from every prior package in this phase.
- **The Pipeline is not yet invoked automatically by anything** - it
  is available to any caller holding a `PipelineRequest`, but no
  automatic trigger (a Connector receiving external input, a
  Scheduler tick, or similar) exists yet; wiring one is a natural
  candidate for a future package.
- **`request.conversation`'s message content is never inspected** -
  the Pipeline passes the `ConversationSession` through unchanged into
  `ContextBuilder.with_conversation(conversation.id)`, which itself
  only ever reads the conversation's `id`; nothing in this package's
  Version 1 orchestration reads message text or role.
- The repository's stray `argus/` duplicate tree and legacy
  pre-Factory files remain unresolved, out of scope per the Founder's
  explicit repository rules.

---

## Future Expansion

- Wire the Reasoning Engine and Decision Engine into `run()` once a
  future package's work order explicitly asks for that integration -
  populating `PlanningSession.goals`/`.constraints` from real
  reasoning/decision output, rather than leaving them permanently
  empty, is the natural next step once that dependency is authorized.
- Wire an automatic trigger (a Connector, a Scheduler tick, or
  similar) to call `CognitivePipeline.run()` on incoming external
  input, once a future package's work order explicitly asks for that
  integration - Version 1 only makes the call possible for a caller
  that already has a `PipelineRequest` in hand.
- Consider whether `PipelineResult` should eventually carry a
  reference back to the originating `PipelineRequest.request_id` as a
  named field rather than only through `metadata["request_id"]`, if a
  future package finds the metadata-based traceability insufficient.
- Consider whether a dedicated `PipelineExecutionError` subtype per
  failing collaborator (a `Planner`-specific variant, as opposed to
  the current single wrapper) becomes useful once the Pipeline gains
  more than one delegate to fail against.

---

## Release Rules

Per the Founder's explicit instruction: no commit, tag, or push was
performed. `CORE_SERVICES_VERSION` was not changed by this package -
it remains `"0.2.4"`. This package is not reported as complete or
released - implementation ends after successful local verification;
final validation, integration, release, version update, commit, and
tag are the Founder's responsibility against the live repository.
