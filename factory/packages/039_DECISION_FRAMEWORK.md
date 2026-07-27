# Package 039 — Decision Framework

## Objective

Introduce the Decision domain: a passive record of a question, its available options, the selected outcome, and the reasoning that led to it. "A Decision captures a question, the available options, the selected outcome, and the reasoning that led to it." Passive domain objects only — no AI, no execution, no scoring, no reasoning engine. This package establishes the architecture only.

## A Genuine Naming Collision, Resolved Per Explicit Founder Direction

Before any code was written, pre-flight verification discovered that `argus/decision/` is not an empty directory — it is the live **Decision Engine**, introduced in Package 021 and wired into `bootstrap.py` as a core service. It already defines a class named `Decision` (the immutable outcome of evaluating one or more `ReasoningResult` objects against registered `DecisionRule`s — fields `decision_type`, `decision_id`, `matched_rules`, `reasoning_results`, `metadata`), plus `DecisionEngine`, `IDecisionEngine`, `DecisionRule`, `DecisionPredicate`, and a five-member exception hierarchy rooted at `DecisionError`. `decision.py`, `interfaces.py`, `exceptions.py`, and `__init__.py` all already existed with this content.

This package's own work order asks for a class named `Decision`, in a module named `decision.py`, inside `argus/decision/` — but describing a structurally and semantically unrelated concept: a captured question/options/outcome/reasoning record, closer in shape to `Goal` (038) than to anything in the Decision Engine. Building it as specified, literally, would have meant overwriting `argus/decision/decision.py`, `interfaces.py`, `exceptions.py`, and `__init__.py` with content that redefines `Decision` — silently breaking the live Decision Engine core service, its bootstrap wiring, and its own existing test suites (`tests/test_decision.py`, `test_decision_engine.py`, `test_decision_rule.py`, plus `tests/test_bootstrap.py`'s own Decision Engine assertions). This is a real regression, not a stylistic judgment call of the kind resolved silently in Packages 036–038 (field ordering, enum defaults, and so on) — so implementation paused and the Founder was consulted directly before any file was written.

Per explicit Founder direction: *"Package 021 already defines the canonical Decision package. Do not replace it or introduce a conflicting `Decision` type. Instead, extend the existing package by introducing a separate historical decision model (using non-conflicting names that fit the package conventions) while preserving complete backward compatibility with the Decision Engine and all existing interfaces. No existing runtime behavior should change."*

This package's own model is therefore named **`DecisionRecord`** throughout — `DecisionRecord`, `DecisionRecordStatus`, `DecisionRecordPriority`, `DecisionRecordMetadata`, `DecisionRecordBuilder`, `IDecisionRecordBuilder`, `DecisionRecordError`, `InvalidDecisionRecordError` — and `argus/decision/` is *extended*, not replaced:

- `metadata.py`, `builder.py`, `status.py`, `priority.py` did not already exist in `argus/decision/` and are created with exactly the filenames this package's own work order specifies.
- `decision.py` already existed (Decision Engine's own `Decision`) — the new value object lives in a new file, `decision_record.py`, instead. This is the one filename deviation from the work order's own literal list, forced by the collision, and it is the minimum deviation that eliminates it.
- `__init__.py`, `interfaces.py`, and `exceptions.py` already existed — each is extended additively (new imports/exports/classes appended after the existing content, under a clearly marked "Package 039 additions" section) rather than replaced. Every symbol Package 021 already exported is untouched, in its original position, with its original behavior.
- `engine.py` and `rule.py` (Decision Engine internals with no work-order equivalent in this package) are untouched entirely.

Verification confirms this: `git diff --stat -- argus/decision/decision.py argus/decision/engine.py argus/decision/rule.py` is empty, `tests/test_decision.py`/`test_decision_engine.py`/`test_decision_rule.py`/`test_bootstrap.py` (116 tests, all pre-existing) all still pass unmodified, and `coverage run --source=argus.decision` reports 100% across all eleven modules in the package — the seven pre-existing Decision Engine modules and the four new/extended ones.

## Architectural Position

Current organizational hierarchy:

```
Workspace -> Project -> Goal -> Plan -> Task
```

New conceptual layer:

```
Project
  ├──► Goal ──► Plan ──► Task
  └──► DecisionRecord
```

A DecisionRecord belongs to a Project. Future versions may also associate DecisionRecords with Goals, Plans, or Tasks. Per this package's own explicit instruction, those relationships are not implemented — no field on `DecisionRecord` references `Project`, `Goal`, `Plan`, or `Task` in Version 1.

## Package (Extended, Not New)

`argus/decision/` after this package:

```
argus/decision/
    __init__.py            (extended — Package 021 content unmodified, Package 039 additions appended)
    decision.py             (unmodified — Package 021's own Decision, the Decision Engine's outcome value object)
    decision_record.py      (new — Package 039's own DecisionRecord)
    engine.py                (unmodified — Package 021's own DecisionEngine)
    rule.py                  (unmodified — Package 021's own DecisionRule)
    metadata.py              (new — DecisionRecordMetadata)
    builder.py                (new — DecisionRecordBuilder)
    status.py                  (new — DecisionRecordStatus)
    priority.py                 (new — DecisionRecordPriority)
    interfaces.py             (extended — IDecisionEngine unmodified, IDecisionRecordBuilder appended)
    exceptions.py              (extended — DecisionError hierarchy unmodified, DecisionRecordError hierarchy appended)
```

## DecisionRecord

Immutable value object. Fields: `decision_id`, `title`, `question`, `status`, `priority`, `metadata` — every field defaults, metadata last, no behavior. `title`/`question` (not `name`/`description`) is a literal reading of this package's own distinct field list — a DecisionRecord's defining content is the question being decided, not a general-purpose description. Mirrors `Goal`'s (038) "value object with a dedicated builder" shape exactly, one field for one field.

## DecisionRecordStatus

Plain `Enum`, five members: `PENDING`, `IN_REVIEW`, `APPROVED`, `REJECTED`, `ARCHIVED`. No transition logic. `PENDING` is the default (first-listed member, per this codebase's own convention) — a DecisionRecord awaiting review is the natural starting state for a posed-but-undecided question.

## DecisionRecordPriority

Plain `Enum`, NOT an `IntEnum`, four members: `LOW`, `NORMAL`, `HIGH`, `CRITICAL`. No ordering behavior — verified via `TypeError` on `<`/`>` comparisons. "Default should follow the same convention established in the Goal framework" — `GoalPriority` (038) defaults to `NORMAL`, not `LOW`, the first deliberate exception to the "first-listed member is the default" convention. This package's own instruction makes following that exception explicit rather than inferred: `DecisionRecordPriority` also defaults to `NORMAL`.

## DecisionRecordMetadata

Immutable. Fields, in order: `created_at`, `version`, `correlation_id`, `owner`, `tags`, `extra`. "Follow the metadata conventions established by Project, Workspace, and Goal" — this package's own work order names the precedent directly, exactly as Package 038's own instruction did, leaving no genuine tension between the literal listed order (`created_at, owner, correlation_id, version, tags, extra`) and the established order. `DecisionRecordMetadata` follows `ProjectMetadata`'s (036) / `WorkspaceMetadata`'s (037) / `GoalMetadata`'s (038) identical order a fourth time. `owner`/`tags` remain system-managed, not settable via `DecisionRecordBuilder`, matching every sibling metadata module's identical precedent.

## DecisionRecordBuilder

Mutable fluent builder — the only mutable object in this addition. Responsibilities: assign title, assign question, assign status, assign priority, assign metadata, build immutable DecisionRecord. `with_priority()` is implemented (unlike `with_owner()`/`with_tags()`), since `priority` is a top-level field and this package's own Responsibilities list names "assign priority" as its own bullet — exactly `GoalBuilder`'s (038) own reasoning. No `with_decision_id()`.

## Integration

No runtime behavior. No Planner, Execution, Capability, Bootstrap, Workspace, Project, Goal, or Response changes. No new core service, no new bootstrap wiring — `IDecisionRecordBuilder` does not inherit `IService`, mirroring `IGoalBuilder`/`IProjectBuilder`/`IWorkspaceBuilder`. Introduces the DecisionRecord model only, additively, inside the pre-existing `argus/decision/` package.

## Dependency Graph

`decision_record.py` depends only on `status.py`, `priority.py`, `metadata.py` (all new, dependency-free leaves). `builder.py` depends on `decision_record.py`, `status.py`, `priority.py`, `metadata.py`, `exceptions.py`, `interfaces.py`. None of the four new modules import `decision.py`, `engine.py`, or `rule.py` — DecisionRecord is a fully independent leaf from the Decision Engine, sharing only the package directory and (via the extended `__init__.py`) the same public import surface.

## Ownership Hierarchy

`Project` owns `DecisionRecord`s (documented relationship only — no field implements it in Version 1). `DecisionRecord` owns nothing in Version 1.

## Future Relationship

A DecisionRecord will eventually own or reference: Options, Evidence, Supporting documents, Confidence, Rationale, Outcome, Review history. Not implemented — documented only, per this package's own explicit instruction.

## Real-World Examples

A DecisionRecord for Just Tallow: "Should we switch packaging vendors for Q3?" (question), title "Vendor selection," status `IN_REVIEW`, priority `HIGH`. A DecisionRecord for ArgusOS itself: "Should Package 039's Decision domain reuse the Decision Engine's own `Decision` name?" (question), title "Decision Framework naming," status `APPROVED`, priority `NORMAL` — the resolution recorded in this very document.

## Engineering Decisions

1. **Naming collision resolved via `DecisionRecord`, not `Decision`, per explicit Founder direction** — see the dedicated section above for the complete record.
2. **`decision.py` → `decision_record.py`; `__init__.py`/`interfaces.py`/`exceptions.py` extended, not replaced** — the minimum-deviation resolution: every filename the work order specifies that was actually free (`metadata.py`, `builder.py`, `status.py`, `priority.py`) is used exactly as named; only the one colliding filename is renamed, and the three shared cross-cutting files are extended additively rather than overwritten.
3. **`DecisionRecordMetadata`'s field order follows Project/Workspace/Goal's identical precedent**, directly named by this package's own work order.
4. **`DecisionRecordPriority` defaults to `NORMAL`, not `LOW`**, per explicit instruction to match `GoalPriority`'s own established exception.
5. **`with_priority()` is implemented; `with_owner()`/`with_tags()` are not** — identical reasoning to `GoalBuilder` (038).
6. **`DecisionRecordError` does not subclass `DecisionError`** — the two hierarchies are deliberately independent, so a caller catching one for Decision Engine failures does not silently also catch unrelated DecisionRecordBuilder validation failures.

## Repository Verification Note

Uploaded repository ("ArgusOS (38).zip") verified fresh — the twenty-fifth consecutive clean pre-flight (015–039). HEAD (`fd142d3`, "Synchronize repository version with v0.3.8 release") is a clean, single-commit descendant of tag `v0.3.8` (which points to `caef3d9`, "Implement Package 038 Goal Framework"). `CORE_SERVICES_VERSION == "0.3.8"` matches tag `v0.3.8`. Pre-flight is also where the `argus/decision/` naming collision was first discovered — see the dedicated section above.

## Files Created

`argus/decision/decision_record.py`, `argus/decision/metadata.py`, `argus/decision/builder.py`, `argus/decision/status.py`, `argus/decision/priority.py`, `factory/packages/039_DECISION_FRAMEWORK.md`, `tests/test_decision_record.py`, `tests/test_decision_record_builder.py`, `tests/test_decision_record_metadata.py`, `tests/test_decision_record_status.py`, `tests/test_decision_record_priority.py`.

## Files Modified

`argus/decision/__init__.py`, `argus/decision/interfaces.py`, `argus/decision/exceptions.py` (all three additively extended only — see above), `factory/ROADMAP.md`, `CHANGELOG.md`, `DEVLOG.md`, `IMPLEMENTATION_REPORT.md`.

`argus/decision/decision.py`, `argus/decision/engine.py`, `argus/decision/rule.py`, `argus/bootstrap.py` — confirmed **unmodified** via `git diff --stat`.

## Test Results

New suites: `python -m pytest tests/test_decision_record*.py -q` → 96 passed. Pre-existing Decision Engine suites re-run unmodified: `tests/test_decision.py`, `test_decision_engine.py`, `test_decision_rule.py`, `test_bootstrap.py` → 116 passed, zero changes. Full suite: `python -m pytest` → 2,630 passed, 38 subtests passed. `python -m unittest discover -s tests` → 2,542 passed. `python -m unittest discover -s argus/tests` → 64 passed, unchanged. `python main.py` → exit 0.

## Coverage

`coverage run --source=argus.decision -m pytest`: 100% across all eleven modules in `argus/decision/` (274 statements total) — the seven pre-existing Decision Engine modules and the four new/extended ones.

## Known Limitations

- No ownership relationship between `Project` and `DecisionRecord` is implemented — documented only.
- `owner`/`tags` are not settable through `DecisionRecordBuilder`.
- No transition logic on `DecisionRecordStatus`, no ordering behavior on `DecisionRecordPriority`.
- `DecisionRecord` and `Decision` (Decision Engine) coexist in the same package under different names — a future reader must know both exist; this is a direct, documented consequence of the naming collision resolution, not an oversight.
- No persistence, no concurrency, no scheduling, no runtime behavior of any kind.

## Release Rules

No commits were created. No tags were created. `CORE_SERVICES_VERSION` remains `"0.3.8"`, unchanged. Repository is ready for architectural review.
