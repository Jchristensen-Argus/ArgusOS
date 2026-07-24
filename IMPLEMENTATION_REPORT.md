# ArgusOS Implementation Report — Package 008: Scheduler Service

## 1. Architecture Summary

Package 008 adds `argus/scheduler/`, ArgusOS's time-orchestration service. `Scheduler` maintains an in-memory registry of `ScheduledTask` objects and executes every due task only when `tick()` is called — no background thread, no timer, fully deterministic under an explicit `now`. Three `Trigger` implementations (`OneShotTrigger`, `IntervalTrigger`, `DailyTrigger`) compute "when is this next due" via a uniform contract, `next_fire_time(after) -> Optional[datetime]`, using strict `>` semantics throughout so no trigger ever double-fires. `IScheduler` inherits `IService`, making Scheduler the first class in the codebase to genuinely implement it — `start()`/`stop()` gate whether `tick()` is permitted to run at all, giving them real behavioral meaning without needing a thread. Every operation publishes a corresponding event on the existing Event Bus (`TaskScheduled`/`TaskStarted`/`TaskCompleted`/`TaskFailed`/`TaskCancelled`/`TaskPaused`/`TaskResumed`), plus the long-reserved `SCHEDULER_TICK` once per `tick()` call. Scheduler is registered as ArgusOS's eighth core service. All 196 pre-existing tests still pass; 85 new tests were added (281 total), all passing under `python -m unittest discover`. No pytest anywhere. `python main.py` starts and shuts down cleanly. Coverage is 100% on every new module except the abstract `Trigger.next_fire_time` stub (never reachable, same shape as every other ABC method stub in this codebase).

## 2. Design Decisions

- **`callback` is a plain Python callable, not routed through Navigator.** `design/specifications/SCHEDULER.md` lists Navigator as a Required Dependency, but Navigator doesn't exist. Rather than invent its contract, v1 Scheduler invokes `ScheduledTask.callback()` directly. Documented as a scope reduction in `factory/packages/008_SCHEDULER_SERVICE.md`, to be revisited once Navigator exists.
- **Strict `>` in every trigger's `next_fire_time`.** Using the same comparison operator uniformly (rather than mixing `>=`/`>` between "first computation" and "post-execution recomputation") is what makes `OneShotTrigger` naturally stop firing after its one execution, with no separate "has this already fired" flag needed.
- **`IntervalTrigger` is fixed-delay, not fixed-rate.** Each next fire time is computed from the actual last check-in (`after`), not a fixed grid. Simpler, and immune to catch-up storms if `tick()` is called infrequently — a deliberate simplicity trade-off, not an oversight.
- **`schedule()` and `resume()` both accept an optional `now`, matching `tick()`.** This was not in my original design and was added reactively after a real bug: without it, `schedule()`'s internal use of live wall-clock time made its own tests non-deterministic (see Section 9, "Deviations," for the full story). All three time-sensitive methods now share the same determinism guarantee.
- **`cancel()` permanently removes a task; `pause()`/`resume()` only toggle `enabled`.** Distinct semantics: a cancelled task's ID can be reused; a paused one cannot be scheduled over.
- **Priority execution order: `CRITICAL` → `HIGH` → `NORMAL` → `LOW`, ties broken by earliest `next_run`.** Fully deterministic given any set of simultaneously-due tasks — required by the "highly testable" instruction.
- **A local `TaskPriority` enum, not `argus.events.EventPriority`.** Task priority and event priority are different concerns that happen to share a shape; reusing `EventPriority` would have coupled `argus.scheduler` to `argus.events`'s priority vocabulary for an unrelated reason.
- **`IScheduler` inherits `IService`, and Scheduler is the first genuine adopter — deliberately, as the ADR-0002 proving ground.** See Section 3.
- **Scheduler is registered in `bootstrap.py` but its `initialize()`/`start()` are never called there.** Nothing in this package calls `tick()` automatically, so starting it during bootstrap would have no behavioral effect while also being bootstrap's first exercise of the exact `IService`/`LifecycleManager` pairing ADR-0002 is watching for trouble in. The IService contract is instead proven correct through direct unit tests.

## 3. IService Adoption and the ADR-0002 Finding

Per your standing instruction from the ADR-0002 discussion — leave `IService` unchanged, let the first real adopter be the proving ground, revisit only if confirmed — Scheduler implements `status()` exactly as the interface requires: a self-tracked internal `LifecycleState`, with no connection to whatever a `LifecycleManager` tracks for the same registered name.

**Finding: the duplication concern is confirmed empirically, not just theoretically.** `tests/test_scheduler.py::IServiceLifecycleDivergenceTests` registers a `Scheduler` with a real `LifecycleManager` the way `bootstrap.py` does, then calls `scheduler.initialize()`/`start()` directly (a realistic action — nothing in `IScheduler`'s contract discourages it). Result: `lifecycle_manager.status("scheduler")` still reports `REGISTERED` while `scheduler.status()` reports `RUNNING`. The two disagree, and nothing detects it.

`bootstrap.py` itself avoids the problem by construction (it registers Scheduler but never calls its `initialize()`/`start()`), but that's a discipline maintained by convention, not enforced by the framework. This finding is appended to `design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md` under "Empirical Finding (Package 008)". **ADR-0002's Status remains `Proposed`**, per your instruction — I did not change it. See Section 8 for the recommended next step.

## 4. Files Created

- `argus/scheduler/__init__.py`, `exceptions.py`, `interfaces.py`, `scheduler.py`, `task.py`, `triggers.py`
- `factory/packages/008_SCHEDULER_SERVICE.md`
- `tests/test_scheduler.py`, `tests/test_scheduler_task.py`, `tests/test_triggers.py`

## 5. Files Modified

- `argus/bootstrap.py` — constructs and registers Scheduler as the eighth core service; `CORE_SERVICES_VERSION` bumped `"0.0.7"` → `"0.0.8"`.
- `argus/events/event_types.py` — added seven `TASK_*` members; `SCHEDULER_TICK` (reserved since Package 003) is now used.
- `tests/test_bootstrap.py` — extended to eight core services.
- `CHANGELOG.md`, `DEVLOG.md` — Package 008 entries appended.
- `design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md` — empirical finding appended (Status left as `Proposed`).

`ARCHITECTURE.md` was **not** modified — `IScheduler` inheriting `IService` was already anticipated by `IService`'s own Package 005 docstring, not a new architectural change. Separately, this work surfaced a real, pre-existing documentation-hygiene issue unrelated to Scheduler itself: this repository contains two unrelated `ARCHITECTURE.md`-adjacent documents. The top-level `ARCHITECTURE.md` describes an older, different pre-Factory project (`Shell`/`Commands`/`AI`/`Identity`/`Memory` components, versioned `v0.0.1` "The Spark" through `v0.0.9` "Intent Detection" in git history — an entirely separate version lineage from the Factory package numbering this session has built). `design/ARCHITECTURE.md`, which sits next to the real, authoritative `design/specifications/*.md` files, is an empty stub. I believe your stated Package list ("001 Identity, 002 Configuration...") traces back to the legacy top-level file, not the Factory history this session has been building and git-verifying (001 Foundation → 002 Bootstrap → 003 Event Bus → 004 Service Registry → 005 Service Lifecycle → 006 Knowledge Service → 007 Memory Service → 008 Scheduler Service, all with continuous commit history). I have not touched either file — this is flagged for your decision, not resolved unilaterally.

## 6. Tests Added

- `tests/test_triggers.py` — 18 tests: `OneShotTrigger` (future/exact/past `run_at`), `IntervalTrigger` (no-`start_at`, repeated advancement, future/past `start_at`, invalid interval), `DailyTrigger` (today/tomorrow rollover, boundary equality, default minute/second, out-of-range validation).
- `tests/test_scheduler_task.py` — 10 tests: field storage, auto-generated `id`, uniqueness, defaults, immutability, `dataclasses.replace` behavior, `TaskPriority` membership.
- `tests/test_scheduler.py` — 56 tests across: IService lifecycle (`initialize`/`start`/`stop`/`status`, illegal-transition guards, `tick()` gating), the empirical `IServiceLifecycleDivergenceTests` (ADR-0002 proof), `schedule()` (id generation, explicit id, duplicates, validation, event publication, explicit-`now` determinism), `cancel()`, `pause()`/`resume()` (including next_run recomputation), `tick()` (one-shot/interval/daily firing, non-refiring, `SCHEDULER_TICK` heartbeat), callback failures (isolated per-task, `TaskFailed` payload, still-rescheduled-on-failure), multiple simultaneous tasks (priority ordering, tie-breaking, partial-due sets), a self-cancelling-callback race-guard test, and `get_task`/`list_tasks` lookup semantics.
- `tests/test_bootstrap.py` — 1 new test confirming Scheduler resolves from the Container.

## 7. Integration Notes

- `Scheduler(event_bus: IEventBus)` — constructed in `bootstrap.py` immediately after the Memory Service.
- Registered in the Container as `"scheduler"`, in the Service Registry as a `ServiceDescriptor` (version `"0.0.8"`), and in the Lifecycle Manager as `LifecycleState.REGISTERED` — consistent with all seven prior core services. Not initialized or started (see Section 2).
- Fully backward compatible: no existing public interface, method signature, or stored data format was changed.
- Scheduler has no dependency on `argus.knowledge` or `argus.memory`, directly or indirectly, per the explicit Non-Goal ("execution history should be made available through events so Memory can subscribe later").

## 8. Merge Instructions

1. Copy `argus/scheduler/` into the repository's `argus/` directory.
2. Copy `factory/packages/008_SCHEDULER_SERVICE.md` into `factory/packages/`.
3. Replace `argus/bootstrap.py`, `argus/events/event_types.py`, and `tests/test_bootstrap.py` with the versions in this delivery.
4. Copy `tests/test_scheduler.py`, `tests/test_scheduler_task.py`, `tests/test_triggers.py` into `tests/`.
5. Replace `design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md` with the version here (adds the empirical finding; Status field is unchanged, still `Proposed`).
6. Append the Package 008 sections already included in the delivered `CHANGELOG.md`/`DEVLOG.md`, or replace the files outright — both are cumulative supersets through Package 007.
7. Run `python -m unittest discover` — expect `Ran 281 tests ... OK`.
8. Run `python main.py` — expect a clean start/shutdown log, exit code 0.
9. Tag the result `v0.0.8`.

**Recommended next step, not part of this merge:** open a dedicated architectural package to resolve `IService.status()`'s duplication, now that ADR-0002's concern is confirmed. Two options are already on record in the ADR: inject `LifecycleManager` + service name so `status()` can delegate, or drop `status()` from `IService` entirely and treat `LifecycleManager` as the sole source of truth everywhere. This is a recommendation for you to act on when ready — I have not implemented either.

## 9. Expected Test Count After Merge

**281 tests** (196 existing + 85 new).

## 10. Deviations from the Work Order

One real deviation, surfaced by a genuine bug rather than a design choice: the work order's requirements list `schedule()` without a `now` parameter. During test-writing, I found that `schedule()`'s internal use of live wall-clock time made it impossible to write deterministic tests — the sandbox's real clock (mid-2026) differs from any fixed test fixture date, so a task scheduled with a fixed `OneShotTrigger(run_at=...)` and a real "now" at schedule time behaved unpredictably. I added an optional `now` parameter to `schedule()` (and, for the same reason, to `resume()`), mirroring `tick()`'s existing pattern. This is additive and backward compatible — omitting `now` preserves the original behavior — but it is a signature addition beyond what the work order specified, made because "deterministic and highly testable" (an explicit requirement) was not achievable without it.

## 11. Test Results

```
Ran 281 tests in 0.032s
OK
```

`python main.py`:
```
2026-07-24 11:06:56 [INFO] argus: ArgusOS application started.
2026-07-24 11:06:56 [INFO] argus: ArgusOS application shutting down.
```
Exit code 0.

## 12. Coverage Summary

| Module | Stmts | Miss | Cover |
|---|---|---|---|
| `argus/bootstrap.py` | 40 | 0 | 100% |
| `argus/events/event_types.py` | 27 | 0 | 100% |
| `argus/scheduler/__init__.py` | 6 | 0 | 100% |
| `argus/scheduler/exceptions.py` | 5 | 0 | 100% |
| `argus/scheduler/interfaces.py` | 21 | 0 | 100% |
| `argus/scheduler/scheduler.py` | 128 | 0 | 100% |
| `argus/scheduler/task.py` | 22 | 0 | 100% |
| `argus/scheduler/triggers.py` | 42 | 1 | 98% (line 68 — the abstract `Trigger.next_fire_time` stub, unreachable) |

Package 008 total: 291 statements, 99.7% covered. Full repository (`argus/*`): 958 statements, 97% covered.

## 13. Known Limitations

- No background thread; `tick()` must be driven externally (a future package's responsibility).
- `callback` is a plain callable, not routed through Navigator (doesn't exist yet).
- No retry/backoff for failed callbacks.
- `IntervalTrigger` is fixed-delay; late ticks cause drift, not catch-up.
- Confirmed (Section 3): Scheduler's own `IService` state can diverge from a `LifecycleManager`'s tracking of the same name if the two are updated out of lockstep.

## 14. Repository-Derived Package Metrics (measured, not estimated)

Measured via `git diff --stat/--numstat/--name-status HEAD~2 HEAD` (commits `82a4ef5` + `22ed03d` on top of `6129351`):

- Files Created: 10 (6 `argus/scheduler/*.py`, `factory/packages/008_SCHEDULER_SERVICE.md`, 3 new test files)
- Files Modified: 5 (`argus/bootstrap.py`, `argus/events/event_types.py`, `tests/test_bootstrap.py`, `CHANGELOG.md`, `DEVLOG.md`) + 1 ADR appended (`design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md`)
- Lines Added: 1,893 (1,854 + 39 for the ADR append)
- Lines Removed: 31
- Unit Tests: 281 passing (85 new)
- Coverage: 99.7% (Package 008 modules), 97% (full repository)
- Public Classes: 6 (`ScheduledTask`, `TaskPriority`, `OneShotTrigger`, `IntervalTrigger`, `DailyTrigger`, `Scheduler`)
- Public Interfaces: 2 (`IScheduler`, `Trigger`)
- New Dependencies: 0
- External Libraries: 0 (standard library only)
- Technical Debt: 5 items (see Known Limitations)
- Architecture Deviations: 0 (the `now=` parameter addition is a signature extension, not an architecture deviation; the two-ARCHITECTURE.md finding is flagged, not an architecture change made by this package)

## 15. ADR Recommendation

**Open a dedicated architectural package to resolve `IService.status()`'s duplicate-state risk**, now confirmed empirically per Section 3. This was anticipated by ADR-0002 itself ("whichever service becomes ArgusOS's first genuine IService adopter should also resolve the interface gap this ADR identifies... not resolved by this ADR"). I have not implemented a fix — only confirmed the concern and left both previously-proposed options on record in the ADR for your decision. ADR-0002's Status remains `Proposed`.

**Secondary, unrelated recommendation:** reconcile or formally retire the legacy top-level `ARCHITECTURE.md` (and its sibling root-level docs — `CHARTER.md`, `MISSION.md`, `decisions.md`/`DECISIONS.md`, `todo.md`/`TODO.md`), and populate the empty `design/ARCHITECTURE.md` stub, per Section 5. This predates Package 008 and is unrelated to Scheduler; flagged here only because implementing this package's "only update ARCHITECTURE.md if required" instruction required determining which file that even referred to.
