# ArgusOS Implementation Report — Package 021: Decision Engine

## 1. Package Overview

Package 021 adds `argus/decision/`, ArgusOS's first-generation deterministic decision layer, sitting between the Reasoning Engine (Package 020) and the Planner in the target architecture — "It does not execute decisions. It does not invoke the Planner. It does not use AI or LLMs. Its responsibility is limited to deterministic decision evaluation." `DecisionRule` (an immutable value object: `name`, `predicate`, `priority`, `id`, `description`) and `Decision` (an immutable outcome: `decision_type`, `decision_id`, `matched_rules`, `reasoning_results`, `metadata`) are pure value objects. `predicate` is a plain Python callable supplied directly by the caller — this package implements no interpreter, scripting language, or dynamic code execution of any kind, satisfying "No scripting. No Python execution. No dynamic code generation" by construction. `DecisionEngine` implements six public methods over an injected `IReasoningEngine`: `evaluate()`/`evaluate_all()` run every registered rule, in priority order, against one or more caller-supplied `ReasoningResult` objects — never stopping at first match — producing a `Decision` whose `matched_rules` reports every match and whose `metadata["rule_evaluations"]` reports a complete per-rule trace. A rule's predicate raising an exception aborts the whole evaluation (unlike Memory Integration's best-effort batch philosophy), publishing `DECISION_FAILED` and raising `RuleEvaluationError`. `register_rule()`/`remove_rule()`/`list_rules()`/`decision_summary()` manage the engine's own local rule table. `DecisionEngine` is registered as ArgusOS's 21st core service, inserted between the Reasoning Engine and the Agent Runtime — the third consecutive dependency-driven placement. The injected `IReasoningEngine` is genuinely wired (per the explicit Bootstrap dependency instruction) but not called anywhere in Version 1 — documented explicitly as a deliberate, restrained choice, not an oversight. All 1,120 pre-existing canonical tests still pass unchanged; 1,181 tests total pass under `python -m unittest discover -s tests`, and `python -m pytest` also passes (1,269 passed, 38 subtests passed). `python main.py` starts and shuts down cleanly.

## 2. Repository Verification Note

Before writing any code, the uploaded repository ("ArgusOS (20).zip") was verified fresh against this package's own general pre-flight instruction ("verify repository state, verify version consistency, verify HEAD/tag ancestry, run smoke validation").

No anomaly was found — the seventh consecutive clean pre-flight (015-021). HEAD (`918c91a`, "Synchronize repository version with v0.2.0 release") is a clean, single-commit descendant of tag `v0.2.0` (which points to `46ad30d`, "Implement Package 020 Reasoning Engine"), confirmed via `git merge-base --is-ancestor v0.2.0 HEAD`; `v0.1.9` also confirmed an ancestor of HEAD. `git diff v0.1.9..HEAD --stat` shows exactly the full, expected Package 020 diff (19 files changed) plus the standard version-sync commit — no anomaly. `git status --short` showed a completely clean working tree. Every substantive check passed cleanly: Package 020 (`argus/reasoning/`) present; `python -m pytest` passing (1208 passed, 38 subtests); `python -m unittest discover -s tests` passing (1120); `python -m unittest discover -s argus/tests` passing (64); `python main.py` starting and shutting down cleanly (exit 0); `CORE_SERVICES_VERSION == "0.2.0"` matching tag `v0.2.0`.

Per the Founder's explicit release rules, this implementation was built, tested, and verified entirely within the supplied repository. No `git commit`, `git tag`, push, or git-history modification of any kind was performed, `CORE_SERVICES_VERSION` was not changed by this package, and this package is not being reported as complete — final validation, integration, release, tagging, and git operations are the Founder's responsibility, to be performed against the live repository after independent regression testing.

## 3. Architectural Rationale

No `design/specifications/DECISION_ENGINE.md` exists — the same situation as Packages 002, 009-020. Every structural decision traces to the Founder's explicit work order. The full rationale for each decision below is also recorded in `factory/packages/021_DECISION_ENGINE.md`'s "Architectural Decisions" section, in the source code's own module docstrings, and is only summarized here.

**Decision 1 — `predicate` is a plain Python callable; no rule scripting language exists.** Rather than accepting rule logic as a parsed expression, `DecisionRule.predicate` is a direct Python callable — satisfying "No scripting. No Python execution. No dynamic code generation" by construction, since no code path in this package can execute arbitrary text as code.

**Decision 2 — Priority ordering: lower first, ties broken by registration order.** Fully deterministic, independent of dict iteration order or wall-clock time.

**Decision 3 — `decision_type` is caller-supplied, opaque data.** The Decision Engine has no domain knowledge of what any `decision_type` means, matching "deterministic infrastructure only."

**Decision 4 — `evaluate_all()` runs every rule; no short-circuit on first match.** `matched_rules` (plural) and "explain which rules matched" both imply every match should be reported; `metadata["rule_evaluations"]` gives a complete trace of every rule, matched or not.

**Decision 5 — A raising predicate aborts the call; no best-effort batch.** Unlike `MemoryIntegration.synchronize_all()` (019), a predicate raising on well-formed input indicates a bug in the rule itself, not a foreseeable outcome — the first such failure aborts the whole call, publishes `DECISION_FAILED`, and raises `RuleEvaluationError`.

**Decision 6 — The injected `IReasoningEngine` is wired but not called in Version 1.** This package's Objective describes operating on caller-supplied `ReasoningResult` objects, not a live service queried internally, and `IReasoningEngine` has no zero-argument snapshot method comparable to `IMemoryIntegration.synchronization_status()` to attach blindly.

**Decision 7 — `IDecisionEngine` inherits `IService`, but the criterion independently disagrees.** Like Packages 018 and 020, all six methods are in-memory and ungated — no method gated.

## 4. IService Adoption — Instruction and Criterion Diverge (Third of Four)

`IDecisionEngine` DOES inherit `IService`, per explicit Founder instruction. Like Package 018's Knowledge Graph and Package 020's Reasoning Engine, and unlike Package 019's Memory Integration, applying ADR-0002's criterion independently to this package's actual methods would NOT have suggested adoption on its own: `evaluate()`, `evaluate_all()`, `register_rule()`, `remove_rule()`, `list_rules()`, and `decision_summary()` are all synchronous, in-memory operations with no phase distinction any of them could plausibly be gated on — architecturally indistinguishable from `KnowledgeGraph` (018) and `ReasoningEngine` (020), both zero-gated adopters. None of the six are gated. This is the eleventh `IService` adopter overall and the fourth with zero gated methods (after `IntentRouter`, `KnowledgeGraph`, and `ReasoningEngine`) — appended to `design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md`, extending the pattern where three of the last four directed-adoption packages (018, 020, 021) diverge from the criterion's own independent conclusion, against only one convergent case (019). Its Status remains `Proposed`, per standing instruction.

## 5. Directory Tree (files touched)

```
argus/
    decision/
        __init__.py                        (new)
        rule.py                            (new)
        decision.py                        (new)
        engine.py                          (new)
        interfaces.py                      (new)
        exceptions.py                      (new)
    bootstrap.py                           (modified)
    events/
        event_types.py                     (modified)
design/
    decisions/
        0002_ISERVICE_ADOPTION_CRITERION.md   (modified — appended finding)
factory/
    packages/
        021_DECISION_ENGINE.md              (new)
    ROADMAP.md                              (modified)
tests/
    test_bootstrap.py                       (modified)
    test_decision.py                        (new)
    test_decision_rule.py                   (new)
    test_decision_engine.py                 (new)
argus/tests/test_bootstrap.py               (modified — CORE_SERVICE_NAMES tuple only, per explicit instruction)
CHANGELOG.md                                (modified)
DEVLOG.md                                   (modified)
IMPLEMENTATION_REPORT.md                    (replaced — this file)
```

No file outside this list was created, deleted, moved, or modified. `argus/reasoning/`, `argus/knowledge_graph/`, `argus/memory_integration/`, `argus/planner/`, `argus/runtime/`, `argus/dispatcher/`, `argus/capability/`, `argus/workflow/`, `argus/plugins/`, `argus/connectors/`, `argus/CHANGELOG.md`, `argus/DEVLOG.md`, `argus/IMPLEMENTATION_REPORT.md`, `argus/factory/`, and every legacy pre-Factory file were left completely untouched. `memory/memory_store.json` shows no diff — this package's own bootstrap end-to-end test uses only the purely in-memory Knowledge Graph and Reasoning Engine, touching no disk-backed resource at all.

## 6. Integration Notes

- `DecisionEngine(reasoning_engine, event_bus)` — constructed in `bootstrap.py` immediately after the Reasoning Engine and immediately before the Agent Runtime, genuinely depending on the former for construction (though not calling it — see Section 9).
- This is now the 21st core service constructed in the bootstrap sequence — the third consecutive dependency-driven placement, after Packages 019 and 020 (Packages 017-018 were both purely positional).
- Registered in the Container (`"decision_engine"`), in the Service Registry as a `ServiceDescriptor` (version `"0.2.0"`, the repository's currently released version — see Section 2), and in the Lifecycle Manager as `LifecycleState.REGISTERED` — matching the treatment of all twenty prior core services. `DecisionEngine`'s own `initialize()`/`start()` are NOT called by bootstrap, for the same divergence-avoidance reasoning already applied to every other `IService` adopter.
- `argus/events/event_types.py` extended with three new members: `DECISION_EVALUATED`, `DECISION_CREATED`, `DECISION_FAILED`.
- Naming (`"decision_engine"`) verified against the repository's own `tests/test_bootstrap.py::CORE_SERVICE_NAMES` convention before implementation.
- The repository's pre-existing, known stray duplicate `argus/tests/test_bootstrap.py` had its `CORE_SERVICE_NAMES` tuple synchronized with `"decision_engine"` added, per the standing Repository Rule introduced in Package 011 — and only that tuple.
- Source-inspection confirms `argus/decision/engine.py` contains no `import argus.planner`, `argus.runtime`, `argus.dispatcher`, `argus.plugins`, `argus.capability`, `argus.workflow`, `argus.connectors`, `argus.knowledge_graph`, or `argus.memory_integration` statement anywhere — the only cross-package imports are `argus.events`, `argus.lifecycle.lifecycle.LifecycleState`, and `argus.reasoning` (`IReasoningEngine` for typing/injection, `ReasoningResult` for typing only — `DecisionEngine` never calls any `IReasoningEngine` method).

## 7. Test Results

Canonical suite (`tests/`):
```
python -m unittest discover -s tests
Ran 1181 tests in 0.085s
OK
```

Per this package's explicit testing instruction:
```
python -m pytest
1269 passed, 38 subtests passed in 0.83s
```

The synchronized duplicate `argus/tests/` also verified passing standalone (unaffected by the one-line sync):
```
python -m unittest discover -s argus/tests -p "test_*.py"
Ran 64 tests in 0.014s
OK
```

`pyflakes` on every new/modified module: clean, no warnings.

`python main.py`:
```
[INFO] argus: ArgusOS application started.
[INFO] argus: ArgusOS application shutting down.
```
Exit code 0.

## 8. Coverage Summary

Measured with `coverage.py`, `python -m coverage run -m pytest`:

| Module | Stmts | Miss | Cover |
|---|---|---|---|
| `argus/bootstrap.py` | 84 | 0 | 100% |
| `argus/events/event_types.py` | 81 | 0 | 100% |
| `argus/decision/__init__.py` | 6 | 0 | 100% |
| `argus/decision/exceptions.py` | 6 | 0 | 100% |
| `argus/decision/interfaces.py` | 19 | 0 | 100% |
| `argus/decision/rule.py` | 12 | 0 | 100% |
| `argus/decision/decision.py` | 17 | 0 | 100% |
| `argus/decision/engine.py` | 105 | 0 | 100% |

Package 021 total (all `argus/decision/*` plus touched `argus/bootstrap.py`/`argus/events/event_types.py`): 330 statements, 100% covered — no accepted gaps, reached on the first measurement with no post-hoc correction required. Full `argus/*` coverage: 99% (unchanged from Package 020; remaining gaps are pre-existing and out of scope).

## 9. Engineering Decisions / Deviations from the Work Order

- **`DecisionRule`/`Decision` perform no validation of their own** — pure value objects, matching `ReasoningQuery`/`ReasoningResult`'s (020) "pure leaf" precedent; all validation lives in `DecisionEngine`. See Section 3.
- **`evaluate()` is a convenience delegate to `evaluate_all()`**, not an independently-implemented method — avoids duplicating evaluation logic across two entry points.
- **A raising rule predicate aborts the whole evaluation**, the opposite of `MemoryIntegration.synchronize_all()`'s (019) best-effort batch philosophy — a deliberate, documented divergence since the two failure categories are not analogous (see Section 3, Decision 5).
- **The injected `IReasoningEngine` is held but never called** — a genuine, documented dependency-usage judgment call, not an oversight; the third distinct shape of this question in this codebase (after Packages 018's "not wired" and 020's "wired and used"). See Section 3, Decision 6.
- **`IDecisionEngine` DOES inherit `IService`, and the criterion independently disagrees, for the third time in four packages** — see Section 4.
- **`CORE_SERVICES_VERSION` remains `"0.2.0"`, unchanged by this package.**
- **`argus/tests/test_bootstrap.py` (duplicate tree) synchronized, tuple-only**, per the standing Repository Rule introduced in Package 011.
- **No coverage gap required a post-hoc fix** — 100% was reached on the first `coverage run`, the first package since 017 for which this was true on the initial measurement.

## 10. Known Limitations

- **No persistence** — `DecisionEngine` retains no history of past Decisions; `decision_summary()` reflects only the currently registered rule set.
- **No AI, no machine learning, no probabilistic reasoning** — every Decision is produced by deterministic, caller-supplied Python predicates evaluated in a fixed, documented order.
- **No rule scripting** — predicates are plain Python callables; this package implements no interpreter, DSL, or dynamic code execution.
- **A raising predicate aborts the entire evaluation** — no best-effort, partial-result mode. See Section 3, Decision 5.
- **The injected `IReasoningEngine` dependency is not called anywhere in Version 1.** See Section 3, Decision 6.
- **The Planner does not yet consume the Decision Engine**, per this package's own explicit Version 1 scope limit and "Planner shall remain unchanged" Constraint.
- No concurrency.
- The repository's stray `argus/` duplicate tree (beyond the one explicitly-required `test_bootstrap.py` sync) and legacy pre-Factory files remain unresolved, out of scope per the Founder's explicit repository rules.

## 11. Repository-Derived Package Metrics (measured, not estimated)

Measured via `git diff --stat` against the working tree's unmodified base commit `918c91a` (no commit was made — see Section 2):

- Files Created: 10 (6 `argus/decision/*.py`, `factory/packages/021_DECISION_ENGINE.md`, 3 new test files)
- Files Modified: 9 (`argus/bootstrap.py`, `argus/events/event_types.py`, `design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md`, `factory/ROADMAP.md`, `tests/test_bootstrap.py`, `argus/tests/test_bootstrap.py`, `CHANGELOG.md`, `DEVLOG.md`, `IMPLEMENTATION_REPORT.md`)
- Lines Added: 2,241 / Lines Removed: 148 (measured via `git diff --stat` across all 19 touched files, including this report's own replacement)
- Unit Tests: 1,181 passing in canonical `tests/` (net +61 vs. Package 020's 1,120: +7 `test_decision.py`, +7 `test_decision_rule.py`, +44 `test_decision_engine.py`, +3 `test_bootstrap.py` [38->41])
- Coverage: 100% (Package 021 modules), 99% (full `argus/*`)
- Public Classes: 3 (`DecisionRule`, `Decision`, `DecisionEngine`)
- Public Interfaces: 1 (`IDecisionEngine`)
- New Dependencies: 0
- External Libraries: 0 (standard library only)
- Architecture Deviations: 0 (see Section 9 for documented, non-architectural deviations)

## 12. Pre-Completion Checklist (per the Founder's explicit checklist)

- ✓ **Bootstrap registration** — `DecisionEngine(...)` constructed in `bootstrap.py`, registered in the Container as `"decision_engine"`. Confirmed via `test_bootstrap_registers_decision_engine_in_container`.
- ✓ **Service registration** — recorded as a `ServiceDescriptor` (version `"0.2.0"`) alongside all twenty prior core services.
- ✓ **Lifecycle integration** — registered in the Lifecycle Manager as `LifecycleState.REGISTERED`, not started. Confirmed via `test_bootstrap_decision_engine_is_not_started`.
- ✓ **Reasoning Engine integration** — confirmed via `test_bootstrap_decision_engine_evaluates_reasoning_result_end_to_end`, evaluating a real Reasoning Engine result end-to-end.
- ✓ **No Planner/Runtime/execution/business-logic responsibilities taken on** — confirmed via source inspection: `argus/decision/*.py` contains no import of `argus.planner`, `argus.runtime`, `argus.dispatcher`, `argus.plugins`, `argus.capability`, `argus.workflow`, `argus.connectors`, `argus.knowledge_graph`, or `argus.memory_integration` anywhere.
- ✓ **Event Bus integration** — all three new events verified published at the correct points via `tests/test_decision_engine.py`.
- ✓ **Naming consistency** — `"decision_engine"` verified against the repository's own `CORE_SERVICE_NAMES` convention before implementation.
- ✓ **Regression suite passes** — `python -m unittest discover -s tests` reports `Ran 1181 tests ... OK`; `python -m pytest` reports `1269 passed, 38 subtests passed`.
- ✓ **`python main.py` starts cleanly** — exit code 0.
- ✓ **`pyflakes` clean** — no warnings on any new/modified module.
- ✓ **No unintended repository modifications** — confirmed via `git status`/`git diff --stat`.
- ✓ **`CORE_SERVICES_VERSION` not modified** — confirmed still `"0.2.0"`.
- ✓ **No commit created** — confirmed via `git log` (HEAD unchanged at `918c91a`).
- ✓ **No tag created** — confirmed via `git tag -l` (unchanged: `v0.0.3`-`v0.2.0`, plus `charter-v1.0`).
- ✓ **Repository ready for architectural review** — all regression, smoke, and pyflakes checks pass locally; final integration, version bump, commit, and tag remain the Founder's responsibility.

## 13. Concise Implementation Summary

Package 021 adds `argus/decision/`: `DecisionRule`/`Decision` (immutable value objects) and `DecisionEngine(IService)`, a deterministic rule-evaluation layer over caller-supplied `ReasoningResult` objects. `predicate` is a plain Python callable — no scripting, no `eval()`/`exec()`, no dynamic code generation anywhere in this package. `evaluate()`/`evaluate_all()` run every registered rule, in priority order, never stopping at first match, producing a `Decision` with a complete matched/not-matched trace; a raising predicate aborts the whole call rather than being tolerated best-effort, the deliberate opposite of Package 019's own batch philosophy. None of the six public methods are gated on `RUNNING` — the fourth zero-gated `IService` adopter in this codebase, and the third of four consecutive directed-adoption packages to diverge from ADR-0002's own criterion. `DecisionEngine` holds an injected `IReasoningEngine` (per explicit Bootstrap instruction) but does not call it anywhere in Version 1 — a documented, deliberate choice, not an oversight. `DecisionEngine` is inserted between the Reasoning Engine and the Agent Runtime in bootstrap's construction order — the third consecutive dependency-driven placement. `argus/planner/`, `argus/runtime/`, and every other pipeline module are untouched; "Planner shall remain unchanged," and per explicit instruction it does not yet consume the Decision Engine. 1,181 tests pass in `tests/` (`python -m pytest` also passes: 1,269 passed, 38 subtests), 100% coverage across all Package 021 modules, reached on the first measurement. Built and verified entirely within the Founder-supplied repository; no commit, tag, push, or git-history change was made, and `CORE_SERVICES_VERSION` was not advanced, per instruction.

## 14. Architectural Observations

- This package's IService finding extends the pattern Package 020's own finding first identified: three of the last four directed-adoption packages (018, 020, 021) diverge from ADR-0002's own criterion, against one convergent case (019). The recommendation to formally separate "adoption" from "gating" as distinct questions now rests on four consecutive data points rather than three, making it progressively harder to treat the ADR's current combined framing as adequate.
- This is the third consecutive core-service placement that is genuinely dependency-driven rather than purely positional (after Packages 019 and 020) — ArgusOS's most recent three insertions have all required a live reference to the immediately preceding service, a notably different pattern from Packages 013-018's mostly-positional insertions.
- The "injected but not called" resolution (Section 3, Decision 6) is the direct architectural counterpart to Package 020's own "injected and genuinely used" resolution for its Memory Integration dependency — read together, the two packages demonstrate that an explicit Bootstrap "depends on" instruction does not automatically imply the dependency must be exercised in the same package; whether it is exercised turns on whether the *specific* injected interface actually offers something safe and meaningful to call blindly, which this package's own careful comparison (IMemoryIntegration.synchronization_status() vs. IReasoningEngine's parameterized methods) worked out concretely rather than by analogy alone.
- The "raising predicate aborts the call" decision (Section 3, Decision 5) is a useful data point for any future package facing a similar "is this failure expected/common, or exceptional/a bug" question when deciding between Package 019's best-effort-batch precedent and this package's fail-fast one: the deciding factor here was whether the input causing the failure was foreseeable given the domain (an unsynchronized memory key is foreseeable; a well-formed ReasoningResult breaking a rule's own logic is not).
- The "currently-unowned architectural gap" flagged in Packages 011 through 020's own reports — nothing yet takes a raw user message all the way through classification, planning, execution, and external communication automatically — remains open after this package. ArgusOS now has a complete, working path from Memory through Knowledge, Reasoning, and deterministic Decision-making, though the Planner's own explicit non-consumption of both the Reasoning Engine and now the Decision Engine (per each package's own Version 1 scope limit) means that path still terminates one step short of influencing an actual Plan.
