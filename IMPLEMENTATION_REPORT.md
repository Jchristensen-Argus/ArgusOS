# ArgusOS Implementation Report — Package 033: Capability Framework

## 1. Package Overview

Package 033 introduces the Capability Framework. "A Capability represents a pluggable unit of functionality that can eventually execute specific types of Tasks. For Package 033: No real work is performed. No tools are invoked. No AI is called. No external APIs are used. The framework simply establishes the contracts and registration mechanism." Pre-flight verification surfaced a direct naming collision: `argus/capability/` already exists, introduced by Package 013 for a different purpose (intent-routing metadata), and is deeply integrated across `IntentDispatcher`, `Planner`, `PluginManager`, `ConnectorManager`, `AgentRuntime`, and `KnowledgeGraph`. Per the Founder's explicit mid-implementation directive — "Do not create a parallel package or replace the existing implementation... evolve those classes rather than duplicating them... Keep the package as the single source of truth for capabilities" — this package extends the existing Package 013 domain in place rather than replacing or duplicating it. `Capability` (`argus/capability/capability.py`) gained two new, additively-defaulted fields, `version: str = "1.0"` and `capability_metadata: CapabilityMetadata`, declared last; every pre-existing field is unchanged. `CapabilityMetadata` (`argus/capability/metadata.py`, new) mirrors the codebase's five other metadata value objects exactly. `CapabilityBuilder` / `ICapabilityBuilder` (`argus/capability/builder.py`, new; `argus/capability/interfaces.py`, modified) is the first dedicated builder `Capability` has ever had. `CapabilityRegistry` (`argus/capability/registry.py`) gained `get_by_name()` and duplicate-name rejection in `register()`. `ExecutionEngine.__init__()` (`argus/execution_engine/engine.py`) gained a new, required `capability_registry: ICapabilityRegistry` parameter, stored but never called — "No dispatch. No execution. No lookup. No behavior changes." `argus/bootstrap.py` passes the existing `capability_registry` singleton into `ExecutionEngine`'s constructor; no new core service was registered and `CORE_SERVICES_VERSION` remains `"0.3.2"`. 2,036 tests total pass under `python -m unittest discover -s tests`, and `python -m pytest` also passes (2,124 passed, 38 subtests passed). `python main.py` starts and shuts down cleanly.

## 2. Repository Verification Note

Before writing any code, the uploaded repository ("ArgusOS (32).zip") was verified fresh against this package's own general pre-flight instruction ("verify repository state, verify version consistency, verify HEAD/tag ancestry, run smoke validation").

No repository-state anomaly was found — the nineteenth consecutive clean pre-flight (015-033). HEAD (`194c6e4`, "Synchronize repository version with v0.3.2 release") is a clean, single-commit descendant of tag `v0.3.2` (which points to `4dbd2bb`, "Implement Package 032 Execution Engine"), confirmed via `git merge-base --is-ancestor v0.3.2 HEAD`. `git diff v0.3.2..HEAD --stat` shows exactly the expected one-line version-sync commit — `CORE_SERVICES_VERSION` moved from `"0.3.1"` to `"0.3.2"`, a patch increment, the Founder's own release choice following Package 032's own integration; no anomaly. Every substantive check passed cleanly: `python -m pytest` passing (2034 passed, 38 subtests, prior to this package's own new tests); `python -m unittest discover -s tests` passing (1946); `python -m unittest discover -s argus/tests` passing (64); `python main.py` starting and shutting down cleanly (exit 0); `CORE_SERVICES_VERSION == "0.3.2"` matching tag `v0.3.2`.

The one genuine anomaly found during pre-flight was architectural, not procedural: `argus/capability/` — the exact package path, and several of the exact file names, this package's own "New Package" section asks to "create" — already exists from Package 013, with a materially different `Capability` shape (intent-routing metadata) already consumed by six other modules. This was surfaced to the Founder directly via a clarifying question rather than resolved unilaterally, per this codebase's own standing "flag genuine ambiguities rather than guess silently" discipline. See Section 3 for the resolution and Section 9 for the full set of downstream engineering decisions it drove.

Per the Founder's explicit release rules, this implementation was built, tested, and verified entirely within the supplied repository. No `git commit`, `git tag`, push, or git-history modification of any kind was performed, `CORE_SERVICES_VERSION` was not changed by this package, and this package is not being reported as complete — final validation, integration, release, tagging, and git operations are the Founder's responsibility, to be performed against the live repository after independent regression testing.

## 3. Architectural Rationale

No `design/specifications/CAPABILITY_FRAMEWORK.md` exists — the same situation as every package since 002 that lacked its own upstream specification file. Every structural decision traces to the Founder's explicit work order and the Founder's own mid-implementation clarifying directive. The full rationale for each decision below is also recorded in `factory/packages/033_CAPABILITY_FRAMEWORK.md`, in the source code's own module docstrings, and is only summarized here.

**Decision 0 — Extend the existing Package 013 `argus/capability/` in place; do not create a parallel package.** The Founder's explicit resolution to the naming collision described in Section 2. Every decision below follows from it.

**Decision 1 — `capability_id` is understood to refer to the pre-existing `id` field, not renamed.** Renaming would touch `CapabilityRegistry`, `IntentDispatcher`, `Planner`, `PluginManager`, and every existing test that keys or reads by `.id` today — a change far larger than "preserving backward compatibility wherever practical" calls for. The same "work order names differ from the established convention; normalize to the convention and document it" resolution this codebase has applied repeatedly.

**Decision 2 — `capability_metadata: CapabilityMetadata` is added as a new, second field rather than retyping the pre-existing `metadata: Mapping[str, Any]` field.** `tests/test_capability.py`'s own pre-existing `MappingProxyType`/subscript/defensive-copy assertions depend on `metadata` staying a plain mapping; retyping it would be a genuine, not cosmetic, backward-compatibility break.

**Decision 3 — `CapabilityBuilder` gained `with_intent_type()`/`with_intent_types()`/`clear_intent_types()`/`with_action_kind()`/`with_workflow_id()`/`with_enabled()`, not individually named in this package's own six-item Responsibilities list.** The fourth recurrence of the "Responsibilities list under-specifies the method surface" pattern (029, 031, 032) — without these, the builder could never set `Capability`'s own pre-existing required (no-default) fields `intent_types`/`action_kind`, making it unable to build a usable Capability.

**Decision 4 — `CapabilityBuilder.with_id()` was implemented, despite no sibling builder (`RelationshipBuilder`, `ExecutionResultBuilder`, `TaskBuilder`) exposing an equivalent for its own object's identity field.** This package's own Responsibilities list explicitly names "assign id" as one of its six items, unlike any of those three siblings' own lists — a deliberate, documented divergence from precedent, justified by explicit instruction rather than silently applied.

**Decision 5 — `CapabilityRegistry.register()` now rejects duplicate names, a genuine behavior change to pre-existing (013) code, breaking two real tests.** Implemented as specified per this package's own explicit "Duplicate names are rejected" requirement; the two affected fixtures in `tests/test_planner.py` were given distinct names rather than the requirement being skipped — the same "the test itself, not the design, needed to change" resolution Package 031 already applied. A full `python -m pytest` run confirmed these were the only two tests anywhere in the repository affected.

**Decision 6 — `ExecutionEngine.__init__()`'s new `capability_registry` parameter is required, with no default.** The work order's own Integration section states "Accept: CapabilityRegistry" with no mention of optionality, and every call site in this codebase always has a real `CapabilityRegistry` available — there is no genuine "no registry yet" case to accommodate defensively.

## 4. IService Adoption

None new. `ICapabilityBuilder` does not inherit `IService` — the same "not an IService" shape every prior builder interface in this codebase (`ICognitiveContextBuilder`/`IPlanningSessionBuilder`/`ITraceBuilder`/`ITaskBuilder`/`IRelationshipBuilder`/`IExecutionResultBuilder`) already established. `ICapabilityRegistry` remains a plain `ABC`, unchanged since Package 013. `IExecutionEngine` remains an `IService` adopter, unchanged in adoption status by this package — its constructor gained a stored dependency, not a gate; `execute()` remains ungated, the sixth zero-gated adopter and fifth divergent ADR-0002 case, both facts established at Package 032 and unaffected here. No new entry was added to `design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md` — this package introduces no new `IService` adopter and changes no adopter's own gating behavior.

## 5. Directory Tree (files touched)

```
argus/
    capability/
        __init__.py                          (modified)
        capability.py                        (modified)
        interfaces.py                        (modified)
        registry.py                          (modified)
        metadata.py                          (new)
        builder.py                           (new)
    execution_engine/
        engine.py                            (modified)
        interfaces.py                        (modified)
    bootstrap.py                             (modified)
factory/
    packages/
        033_CAPABILITY_FRAMEWORK.md          (new)
    ROADMAP.md                               (modified)
tests/
    test_capability_builder.py               (new)
    test_capability_metadata.py              (new)
    test_capability.py                       (modified)
    test_capability_registry.py              (modified)
    test_execution_engine.py                 (modified)
    test_agent_service.py                    (modified)
    test_bootstrap.py                        (modified)
    test_planner.py                          (modified)
CHANGELOG.md                                 (modified)
DEVLOG.md                                    (modified)
IMPLEMENTATION_REPORT.md                     (replaced — this file)
```

No file outside this list was created, deleted, moved, or modified. Per this package's own explicit constraints — "Do not execute capabilities. Do not modify Task. Do not modify Plan. Do not redesign ExecutionEngine, Pipeline, Response, Runtime, ExecutionTrace. Do not introduce plugins, persistence, or AI. Do not call tools or APIs" — `argus/task/`, `argus/task_relationship/`, `argus/planner/`, `argus/planning/`, `argus/pipeline/`, `argus/response/`, `argus/trace/`, `argus/runtime/`, `argus/agent/service.py`, `argus/dispatcher/`, `argus/plugins/`, `argus/connectors/`, `argus/knowledge_graph/`, every `argus/execution_engine/` file other than `engine.py`/`interfaces.py`, `argus/tests/test_bootstrap.py`, and `argus/events/event_types.py` were left completely untouched — confirmed via `git diff --stat` showing zero lines changed in any of them.

## 6. Integration Notes

- `argus/bootstrap.py` passes the already-constructed `capability_registry` singleton into `ExecutionEngine(capability_registry=capability_registry)` — genuine dependency injection of the same object the container resolves under `"capability_registry"`, not a second instance. No new core service was registered; `CapabilityRegistry` has been a core service since Package 013. `CORE_SERVICES_VERSION` remains `"0.3.2"`, unchanged by this package.
- `ExecutionEngine.execute()`'s own four-step sequence, unchanged since Package 032, is completely untouched — only `__init__()` changed, confirmed via `git diff` touching exactly one method.
- `CapabilityRegistry.register()`'s new duplicate-name check runs after the pre-existing duplicate-id check, raising the same `DuplicateCapabilityError` either way — no new exception type.
- `CapabilityBuilder.with_metadata()` populates `CapabilityMetadata.extra`, not the pre-existing bare `metadata` field — the two "metadata" concepts on `Capability` are never merged.
- `argus/capability/metadata.py` remains a pure, dependency-free leaf, matching every other metadata value object in this codebase; `argus/execution_engine/engine.py`'s new dependency on `argus.capability.interfaces` is one-directional and inert — no method in `argus.capability` imports or calls into `argus.execution_engine` in either direction.
- Source-inspection confirms no file outside `argus/execution_engine/`, `argus/bootstrap.py`, and the new/modified test files imports anything new from `argus.capability` as a result of this package.

## 7. Test Results

New capability metadata/builder suites:
```
python -m pytest tests/test_capability_builder.py tests/test_capability_metadata.py -q
67 passed in 0.05s
```

Modified capability/execution_engine/bootstrap/agent/planner suites:
```
python -m pytest tests/test_capability.py tests/test_capability_registry.py tests/test_execution_engine.py tests/test_agent_service.py tests/test_bootstrap.py argus/tests/test_bootstrap.py tests/test_planner.py -q
```
(all passing as part of the full run below)

Canonical suite (`tests/`):
```
python -m unittest discover -s tests
Ran 2036 tests in 0.157s
OK
```

Per this package's explicit testing instruction:
```
python -m pytest
2124 passed, 38 subtests passed in 1.40s
```

The duplicate `argus/tests/` also verified passing:
```
python -m unittest discover -s argus/tests
Ran 64 tests in 0.016s
OK
```

`python main.py`:
```
[INFO] argus: ArgusOS application started.
[INFO] argus: ArgusOS application shutting down.
```
Exit code 0.

## 8. Coverage Summary

Measured with `coverage.py`, `python -m coverage run --source=argus.capability,argus.execution_engine.engine,argus.execution_engine.interfaces,argus.bootstrap -m pytest`:

| Module | Stmts | Miss | Cover |
|---|---|---|---|
| `argus/bootstrap.py` | 96 | 0 | 100% |
| `argus/capability/__init__.py` | 7 | 0 | 100% |
| `argus/capability/builder.py` | 71 | 0 | 100% |
| `argus/capability/capability.py` | 21 | 0 | 100% |
| `argus/capability/exceptions.py` | 4 | 0 | 100% |
| `argus/capability/interfaces.py` | 44 | 0 | 100% |
| `argus/capability/metadata.py` | 14 | 0 | 100% |
| `argus/capability/registry.py` | 70 | 0 | 100% |
| `argus/execution_engine/engine.py` | 35 | 0 | 100% |
| `argus/execution_engine/interfaces.py` | 31 | 0 | 100% |

100% coverage across the entire `argus/capability/` package (231 statements, both new and modified modules) and across every modified `argus/execution_engine/` module and `argus/bootstrap.py` (162 statements) — reached on the first measurement, no post-hoc gap-closing needed.

## 9. Engineering Decisions / Deviations from the Work Order

- **A parallel `argus/capability/` package was not created; the existing Package 013 package was extended in place.** See Section 3, Decision 0 — the single largest deviation from this package's own literal work order, directly instructed by the Founder.
- **`capability_id` is not a real field name; it refers to the pre-existing `id` field.** See Section 3, Decision 1.
- **`capability_metadata` is a new, additive field, not a retyping of the pre-existing `metadata` field.** See Section 3, Decision 2.
- **`CapabilityBuilder` gained a method surface beyond the work order's own six-item Responsibilities list.** See Section 3, Decision 3 — the fourth recurrence of this pattern (029, 031, 032).
- **`CapabilityBuilder.with_id()` was implemented despite no sibling builder exposing an equivalent.** See Section 3, Decision 4 — explicitly justified by this package's own Responsibilities list, not applied by default.
- **`CapabilityRegistry.register()`'s new duplicate-name rejection broke two pre-existing tests, fixed by renaming test fixtures, not by weakening the requirement.** See Section 3, Decision 5.
- **`ExecutionEngine.__init__()`'s new parameter is required, not optional.** See Section 3, Decision 6.
- **`CORE_SERVICES_VERSION` remains `"0.3.2"`, unchanged by this package.**
- **No coverage gap required a post-hoc fix** — 100% was reached on the first `coverage run` across every new and modified file.

## 10. Known Limitations

- **No dispatch model exists yet** — "The framework simply establishes the contracts and registration mechanism." `ExecutionEngine` holds a `CapabilityRegistry` reference but never calls any of its methods; nothing in this codebase yet resolves a `Task` to a `Capability` or invokes one.
- **`Capability` still performs no field validation of its own** — unchanged since Package 013; `CapabilityRegistry.register()` and `CapabilityBuilder`'s own `with_*()` methods remain the only two places validation lives.
- **Two distinct "metadata" concepts now coexist on `Capability`** — the pre-existing (013) `metadata: Mapping[str, Any]` and the new (033) `capability_metadata: CapabilityMetadata` are never merged or reconciled into one field.
- **`capability_id` is not a real field name anywhere in this codebase** — a documented alias for the pre-existing `id` field.
- **No tool invocation, API call, or AI inference of any kind.**
- **`ExecutionEngine` is no longer a fully-empty-constructor core service** — `ResponseEngine` (027) remains the sole surviving example of that shape; `IExecutionEngine`'s own zero-gated-adopter and divergent-ADR-0002-case counts are unaffected, since no method gained a gate.
- No execution, no scheduling, no persistence, no concurrency — unchanged from every prior package in this phase.
- The repository's stray `argus/` duplicate tree and legacy pre-Factory files remain unresolved, out of scope per the Founder's explicit repository rules.

## 11. Repository-Derived Package Metrics (measured, not estimated)

Measured via `git diff --stat` against the working tree's unmodified base commit `194c6e4` (no commit was made — see Section 2):

- Files Created: 4 (`argus/capability/metadata.py`, `argus/capability/builder.py`, `tests/test_capability_builder.py`, `tests/test_capability_metadata.py`) plus `factory/packages/033_CAPABILITY_FRAMEWORK.md` — 5 total
- Files Modified: 13 (`argus/capability/__init__.py`, `capability.py`, `interfaces.py`, `registry.py`, `argus/execution_engine/engine.py`, `interfaces.py`, `argus/bootstrap.py`, `factory/ROADMAP.md`, `tests/test_capability.py`, `test_capability_registry.py`, `test_execution_engine.py`, `test_agent_service.py`, `test_bootstrap.py`, `test_planner.py`, `CHANGELOG.md`, `DEVLOG.md`) plus `IMPLEMENTATION_REPORT.md` itself (replaced) — 17 total
- Unit Tests: 2,036 passing in canonical `tests/` (net +90 vs. Package 032's 1,946: +57 `test_capability_builder.py`, +10 `test_capability_metadata.py`, +10 `test_capability.py`, +9 `test_capability_registry.py`, +3 `test_execution_engine.py`, +1 `test_bootstrap.py`; `test_agent_service.py`/`test_planner.py` updated in place with no net count change)
- Coverage: 100% (all 10 statement-bearing modules across `argus/capability/`, `argus/execution_engine/engine.py`, `argus/execution_engine/interfaces.py`, and `argus/bootstrap.py`, 393 statements total)
- Public Classes: 1 new (`CapabilityMetadata`), 0 new on `Capability`/`CapabilityRegistry` themselves (extended in place)
- Public Interfaces: 1 new (`ICapabilityBuilder`)
- New Exceptions: 0 (existing `InvalidCapabilityError`/`DuplicateCapabilityError`/`CapabilityNotFoundError` cover every new failure mode)
- New Core Services: 0 — `CapabilityRegistry` has been a core service since Package 013; this package changes what one *other* core service's constructor receives
- New Dependencies: 0 external; `argus/execution_engine/engine.py` gained a new, real, runtime dependency on `argus.capability.interfaces.ICapabilityRegistry`
- External Libraries: 0 (standard library only)
- Architecture Deviations: 1 breaking change, explicitly instructed by the Founder's own mid-implementation directive (extend Package 013's `argus/capability/` in place rather than create a parallel package), fully absorbed; 1 genuine behavior change to pre-existing code (duplicate-name rejection), breaking two pre-existing tests, fixed by updating those tests; 6 documented interpretive judgment calls (see Section 9)

## 12. Pre-Completion Checklist (per the Founder's explicit checklist)

- ✓ **Naming collision with the existing Package 013 `argus/capability/` package surfaced and resolved per Founder direction, not guessed at** — confirmed via the AskUserQuestion exchange and the Founder's own explicit mid-turn directive, both incorporated into every subsequent decision.
- ✓ **Existing `argus/capability/` package extended in place, not duplicated or replaced** — confirmed via `git status` showing `argus/capability/capability.py`/`registry.py`/`interfaces.py`/`__init__.py` as modified, not deleted or shadowed, and `builder.py`/`metadata.py` as new additions within the same package.
- ✓ **`Capability` gained `version`/`capability_metadata` fields, both additively defaulted, every pre-existing field unchanged** — confirmed via `tests/test_capability.py`'s own `BackwardCompatibilityTests` class.
- ✓ **`CapabilityBuilder`/`ICapabilityBuilder` implemented; builder is the only mutable object** — confirmed via `CapabilityBuilder` being the sole class with mutable instance state in `argus/capability/`.
- ✓ **`CapabilityRegistry` extended with `get_by_name()` and duplicate-name rejection, insertion order preserved, duplicate ids still rejected** — confirmed via `tests/test_capability_registry.py`'s own dedicated test coverage.
- ✓ **`ExecutionEngine.__init__()` modified to accept `capability_registry`; no dispatch, no execution, no lookup, no behavior change to `execute()`** — confirmed via `tests/test_execution_engine.py`'s own `ConstructorInjectionTests` class, including the exploding-registry test proving `execute()` never calls it.
- ✓ **Bootstrap wired: `capability_registry` passed into `ExecutionEngine`'s new constructor parameter** — confirmed via `tests/test_bootstrap.py`'s own new test asserting identity between the container's own `capability_registry` and the one `ExecutionEngine` stores.
- ✓ **No Task/Plan changes, no ExecutionEngine/Pipeline/Response/Runtime/ExecutionTrace redesign** — confirmed via `git diff --stat` on `argus/task/`, `argus/planner/`, `argus/planning/`, `argus/pipeline/`, `argus/response/`, `argus/trace/`, `argus/runtime/`, zero lines changed in any of them.
- ✓ **No plugins, persistence, AI, or tool/API calls introduced anywhere in this package** — confirmed via source inspection of every new/modified file.
- ✓ **No new EventTypes** — confirmed via `git diff --stat -- argus/events/event_types.py` showing zero lines changed.
- ✓ **Immutable Capability, registry insertion order, duplicate rejection, lookup by id, lookup by name, bootstrap registration, ExecutionEngine constructor injection all tested** — confirmed via the corresponding dedicated test classes across all new/modified test files.
- ✓ **100% coverage across `argus/capability/` and every modified `argus/execution_engine/`/`argus/bootstrap.py` module** — confirmed via `coverage.py` (393/393 statements).
- ✓ **No regressions** — `python -m unittest discover -s tests` reports `Ran 2036 tests ... OK`; `python -m pytest` reports `2124 passed, 38 subtests passed`; every one of Package 032's own 2,034 passing pytest tests still passes (after the two necessary test-fixture renames in `tests/test_planner.py`).
- ✓ **`python main.py` starts cleanly** — exit code 0.
- ✓ **No unintended repository modifications** — confirmed via `git status`/`git diff --stat`.
- ✓ **`CORE_SERVICES_VERSION` not modified** — confirmed still `"0.3.2"`.
- ✓ **No commit created** — confirmed via `git log` (HEAD unchanged at `194c6e4`).
- ✓ **No tag created** — confirmed via `git tag -l` (unchanged, ending `v0.3.0`, `v0.3.1`, `v0.3.2`).
- ✓ **Repository ready for architectural review** — all regression, smoke, and coverage checks pass locally; final integration, version bump, commit, and tag remain the Founder's responsibility.

## 13. Concise Implementation Summary

Package 033 extends the existing Package 013 `argus/capability/` package in place, per the Founder's explicit mid-implementation directive, rather than creating a parallel package for this package's own differently-shaped work order request. `Capability` gained two new, additively-defaulted fields — `version` and `capability_metadata: CapabilityMetadata` (new, mirroring the codebase's five sibling metadata objects exactly) — with every pre-existing (013) field unchanged. `CapabilityBuilder` / `ICapabilityBuilder` (new) is the first dedicated builder `Capability` has ever had, its method surface extended beyond the work order's own six-item list for the fourth time this codebase has needed to make that call, and its `with_id()` method a deliberate divergence from every sibling builder's own precedent. `CapabilityRegistry` gained `get_by_name()` and duplicate-name rejection in `register()` — a genuine behavior change that broke two pre-existing tests in `tests/test_planner.py`, fixed by renaming test fixtures rather than weakening the requirement. `ExecutionEngine.__init__()` gained a required `capability_registry` parameter, stored but never called by `execute()`, ending its own brief run as this codebase's second empty-constructor core service without changing its ungated status. `argus/bootstrap.py` wires the existing `capability_registry` singleton into `ExecutionEngine`'s new constructor parameter; no new core service was registered and `CORE_SERVICES_VERSION` remains `"0.3.2"`. `argus/task/`, `argus/task_relationship/`, `argus/planner/`, `argus/planning/`, `argus/pipeline/`, `argus/response/`, `argus/trace/`, and `argus/runtime/` remain completely untouched. 2,036 tests pass in `tests/` (`python -m pytest` also passes: 2,124 passed, 38 subtests), 100% coverage across the entire `argus/capability/` package and every modified `argus/execution_engine/`/`argus/bootstrap.py` module (393 statements). Built and verified entirely within the Founder-supplied repository; no commit, tag, push, or git-history change was made, and `CORE_SERVICES_VERSION` was not advanced, per instruction.

## 14. Architectural Observations

- This is the first package in this session's history to use `AskUserQuestion` mid-implementation to resolve a genuine, high-blast-radius architectural collision before writing any code, rather than only during initial pre-flight ambiguity review — a direct consequence of a work order asking to "create" a package, and several specific file names within it, that already existed with a materially different shape and a six-consumer blast radius.
- The "value object with a dedicated builder, every field defaults" family did not gain a new member this package — `Capability` is not new, it predates this pattern's own emergence (Package 013 predates Package 022's `CognitiveContext`, the first member of that family). Instead, this package retrofits that family's shape onto a pre-existing object for the first time, giving `Capability` a dedicated builder five packages after the pattern itself was established.
- The "builder Responsibilities list under-specifies the method surface a builder actually needs" pattern (029, 031, 032) recurred for a fourth time, continuing to firm up as this codebase's own standing precedent — but this package also produced the pattern's first documented *exception*, where a builder's own identity-setting method (`with_id()`) was implemented specifically because the work order named it, unlike three prior siblings that all omit the equivalent by default.
- The "two metadata fields on one object" resolution — adding `capability_metadata` alongside the pre-existing bare `metadata` field rather than retyping it — is a new shape for this codebase, not a repeat of any prior package's own metadata-field-order-normalization precedent (028/029/031/032, all of which reordered a single field's own declared fields, never added a second competing field of the same conceptual name).
- Package 032 named "Execution Engine -> Capability Registry -> [future: Task-to-Capability resolution] -> [future: genuine per-Task outcomes] -> Execution Result" implicitly by inserting the first genuinely new orchestration stage. This package wires up the next arrow in that chain literally — `ExecutionEngine -> CapabilityRegistry` — but, matching the pattern established by every "constructor dependency arrives before behavior" package in this phase, declines to give that reference any actual behavioral consequence, continuing this phase's own practice of naming one more precisely-scoped, still-unbuilt future segment per package rather than building ahead of specification.
