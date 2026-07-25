# Implementation Package 015 - Planner

## Objective

Give ArgusOS a reasoning-only layer that converts an Intent into an
ordered Execution Plan before any capability resolution, dispatch, or
execution occurs. Per the Founder's Package 015 work order:

```
Conversation -> Intent -> Planner -> Execution Plan -> Capability Registry -> Dispatcher -> Action -> Plugin Manager -> Workflow
```

extending Package 014's:

```
Conversation -> Intent -> Capability Registry -> Dispatcher -> Action -> Plugin Manager -> Workflow
```

The Planner performs reasoning only. It never executes workflows,
never dispatches actions, and never calls plugins.

---

## Specification Note

No `design/specifications/PLANNER.md` exists in the repository - the
same situation as Packages 002, 009, 010, 011, 012, 013, and 014. This
package is built directly from the Founder's explicit work order.

---

## Constraints (Explicit, Non-Negotiable)

- The Planner produces planning data only. `argus/planner/planner.py`
  never imports `argus.dispatcher`, `argus.workflow`, or
  `argus.plugins`, and never constructs, obtains, or invokes an
  `Action`, a `Workflow`, or a `Plugin` - verified by test
  (`tests/test_planner.py` and a direct source-inspection assertion in
  `IMPLEMENTATION_REPORT.md`'s Pre-Completion Checklist).
- `validate_plan()`'s only touchpoint with the Capability Registry is
  a read-only `ICapabilityRegistry.contains()` existence check -
  never `register()`, `unregister()`, `get()`, or
  `find_by_intent_type()`. No change was made to `argus/capability/`.
- Version 1 does not optimize, execute, or schedule plans - `Planner`
  has no reordering heuristic, no redundant-step detection, no timing,
  and no recurrence.

---

## Architecture

The target architecture places the Planner *above* Intent
classification and the Capability Registry - conceptually, an Intent
is planned before any of its steps are resolved to real Capabilities.
Construction order in `bootstrap.py`, however, is governed by
dependency order, not diagram position: `Planner` is constructed last
among the fifteen core services, immediately after the Intent
Dispatcher, because it needs a live `ICapabilityRegistry` reference to
perform its one read-only check. This is the same distinction Package
013 already drew for Capability Registry versus Intent Dispatcher -
diagram position describes conceptual data flow, not construction
order.

`PlanStep.required_capability` is a plain capability id string, not a
resolved `Capability` object - the Planner never resolves an
`IntentType` to a `Capability` itself (that remains the Capability
Registry's/Dispatcher's job); it only checks whether a given id is
currently registered. A caller building a Plan's steps is expected to
already know which capability ids it wants to reference (for example,
by first calling `capability_registry.list_capabilities()` or
`find_by_intent_type()` itself) - the Planner does not perform that
lookup on the caller's behalf, keeping its own responsibility limited
to "does this id exist," matching this package's explicit "It should
verify that required capabilities exist. It should NOT invoke them"
instruction.

---

## Architectural Decisions

### 1. `order` is recomputed by Planner, never set directly by a caller

`PlanStep.order` always mirrors a step's actual position within its
Plan's `steps` tuple. `add_step()` appends with `order = len(steps)`;
`remove_step()` renumbers every remaining step to stay contiguous;
`reorder_steps()` reassigns `order` to match the caller-supplied new
sequence. No public method lets a caller set `order` independently of
actual tuple position - avoiding exactly the kind of two-independent-
trackers-of-the-same-fact risk this codebase has been careful about
since `ServiceDescriptor`/`LifecycleManager`'s Package 005
architectural revision and ADR-0002's own recurring theme.

### 2. Any structural mutation resets a Plan's status to CREATED

`add_step()`, `remove_step()`, and `reorder_steps()` all reset
`status` to `PlanStatus.CREATED`, even if the Plan was previously
`VALIDATED` or `FAILED`. This is an inferred business rule, not
specified verbatim by the work order: a Plan's validated/failed status
describes whether its *current* steps were last confirmed against the
Capability Registry, so mutating those steps without invalidating that
status would let a stale, no-longer-accurate status persist silently.
`validate_plan()` must always be re-run after any structural change.

### 3. `PLAN_REMOVED` (a suggested example event) was not added

The work order's Events section lists `PLAN_REMOVED` as an example,
but the Planner's own listed responsibilities have no "delete an
entire Plan" operation for such an event to correspond to - only
step-level `add_step()`/`remove_step()`/`reorder_steps()` are in
scope. All three are folded into a single `PLAN_UPDATED` event instead
(distinguished by a `"change"` payload field:
`"added_step"`/`"removed_step"`/`"reordered"`), per this package's own
"Only add events that provide real architectural value" instruction -
inventing three granular events, or a fourth event with nothing to
fire it, would not have added value a single well-labeled event
doesn't already provide.

### 4. `validate_plan()` failure raises and persists FAILED, but publishes nothing

Mirrors `CapabilityRegistry.register()`'s and `PluginManager.
register()`'s identical "a failed/rejected call raises and publishes
nothing" precedent (Packages 013, 014), rather than
`WorkflowEngine.execute()`'s/`IntentDispatcher.dispatch()`'s "raise
and also publish a distinct *_FAILED event" precedent. `validate_plan()`
is closer in shape to a registry-style validation gate than to a
multi-step execution engine, so the simpler, already-established
precedent was chosen: `PlanValidationError` is raised, and the Plan is
still persisted internally with `status=PlanStatus.FAILED` (queryable
via `get_plan()`), but no event fires for the failed attempt - only a
successful `validate_plan()` call publishes `PLAN_VALIDATED`.

### 5. `PlanStatus.READY` and `PlanStatus.COMPLETED` are defined but unreachable in Version 1

The work order's Domain Model names five status values; only three
(`CREATED`, `VALIDATED`, `FAILED`) are ever produced by any Version 1
Planner method. `READY` and `COMPLETED` are included in the enum
(since the work order names them as part of the status vocabulary)
but reserved for a future package that integrates the Planner with
dispatch and execution-outcome reporting, respectively - the same
"reserved for a future package" treatment Package 012 gave
`workflow_id`s with no registered Workflow behind them yet.

---

## Events

Three new `EventType` members - `PLAN_CREATED`, `PLAN_UPDATED`,
`PLAN_VALIDATED` - judged genuinely useful; `PLAN_REMOVED` was
considered and rejected, per Architectural Decision 3 above.
`PLAN_CREATED` fires once per successful `create_plan()` call.
`PLAN_UPDATED` fires once per successful `add_step()`/`remove_step()`/
`reorder_steps()` call, with a `"change"` payload field identifying
which. `PLAN_VALIDATED` fires only when `validate_plan()` succeeds -
per Architectural Decision 4, a failed validation raises
`PlanValidationError` and publishes nothing.

---

## IService Adoption

`IPlanner` does NOT inherit `IService` - a deliberate, documented
non-adoption, not an oversight, and the third consecutive one
following Capability Registry (013) and Plugin Manager (014).
`Planner` is architecturally identical to Knowledge Service (006),
Memory Service (007), Capability Registry (013), and Plugin Manager
(014): fully usable the instant it is constructed, with nothing for
`start()`/`stop()` to meaningfully gate. See
`argus/planner/interfaces.py`'s Architectural Note and
`design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md`'s newly
appended Empirical Finding, which records this as the third
consecutive new *non*-adopter data point.

---

## Repository Verification Note

The uploaded repository ("ArgusOS (14).zip") passed pre-flight
verification on the first attempt: Package 014 (`argus/plugins/`)
present; HEAD (`5fb57f1`, "Synchronize repository version with v0.1.4
release") confirmed a clean one-commit descendant of tag `v0.1.4`
(which itself points to `6c319ac`, "Implement Package 014 Plugin
Manager") via `git merge-base --is-ancestor`, with `git diff
6c319ac..HEAD --stat` confirming the intervening commit touches only
`argus/bootstrap.py`, 1 insertion/1 deletion; `python -m pytest`
passing (762 passed, 38 subtests) and `python main.py` starting and
shutting down cleanly (exit 0), both before any Package 015 code was
written; `CORE_SERVICES_VERSION == "0.1.4"` confirmed at
`argus/bootstrap.py`.

---

## Specifications Referenced

- factory/packages/014_PLUGIN_MANAGER.md (nearest precedent for a
  metadata/reasoning-only registry that deliberately does not adopt
  `IService`, and for constructing new core services in dependency
  order rather than diagram order)
- factory/packages/013_CAPABILITY_REGISTRY.md (precedent for the
  diagram-position-versus-construction-order distinction this
  package's Architecture section relies on)
- factory/packages/010_WORKFLOW_ENGINE.md (precedent for
  replace-don't-mutate handling of an immutable value object's
  ordered steps, and for a status enum with values a given package
  version does not fully exercise)

---

## Files Created

```
argus/
    planner/
        __init__.py
        plan.py
        step.py
        planner.py
        interfaces.py
        exceptions.py
tests/
    test_plan.py
    test_step.py
    test_planner.py
```

## Files Modified

```
argus/bootstrap.py            (construct + register Planner as 15th
                                core service, immediately after the
                                Intent Dispatcher; depends on the
                                Capability Registry only;
                                CORE_SERVICES_VERSION left at "0.1.4"
                                - not advanced)
argus/events/event_types.py   (3 new event types)
argus/tests/test_bootstrap.py (CORE_SERVICE_NAMES tuple only, per the
                                standing Package 011 rule)
tests/test_bootstrap.py       (CORE_SERVICE_NAMES tuple + 3 new tests)
design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md (Empirical Finding
                                appended; Status remains Proposed)
CHANGELOG.md, DEVLOG.md, IMPLEMENTATION_REPORT.md, factory/ROADMAP.md
```

`argus/dispatcher/`, `argus/capability/`, `argus/workflow/`, and
`argus/plugins/` are unchanged - the Planner's only touchpoint with
any of them is a read-only `ICapabilityRegistry.contains()` call.

---

## Test Totals

759 tests passing via `python -m unittest discover -s tests` (674 from
Packages 002-014, plus 13 new in `test_step.py`, plus 17 new in
`test_plan.py`, plus 52 new in `test_planner.py`, plus 3 new in
`test_bootstrap.py` [20->23]).
`python -m unittest discover -s argus/tests` remains at 64 (duplicate
tree unaffected beyond the standing `CORE_SERVICE_NAMES` sync).
`python -m pytest` also passes: 847 passed, 38 subtests passed.

---

## Coverage

100% line coverage on every new/modified module measured for this
package: `argus/planner/__init__.py`, `argus/planner/plan.py`,
`argus/planner/step.py`, `argus/planner/planner.py`,
`argus/planner/interfaces.py`, `argus/planner/exceptions.py`,
`argus/bootstrap.py`, and `argus/events/event_types.py` - all 100%, no
accepted gaps. Overall repository coverage: 99%, unchanged from
Package 014.

---

## Known Limitations

- `PlanStatus.READY` and `PlanStatus.COMPLETED` are never produced by
  any Version 1 Planner method - reserved for a future dispatch-
  integration and completion-reporting package, per Architectural
  Decision 5.
- `required_capability` is checked for existence only
  (`ICapabilityRegistry.contains()`) - `validate_plan()` does not check
  whether a matching Capability is `enabled`, nor whether it actually
  supports the Plan's originating Intent's `IntentType`. A Plan can
  validate successfully while referencing a disabled or
  semantically-mismatched Capability; catching that is left to a
  future package, consistent with "Version 1 does NOT optimize plans."
- The Planner is not wired to the Capability Registry/Dispatcher path
  in any direction beyond the one read-only check - nothing
  automatically creates a Plan from a resolved Intent, and nothing
  consumes a validated Plan to actually dispatch it. This is the
  expected Version 1 scope boundary, not a defect.
- Plans are held only in memory; nothing persists across process
  restarts.

---

## Future Expansion

- A future package could wire `ConversationManager`/`IntentDispatcher`
  to call `Planner.create_plan()` automatically for every resolved
  Intent, closing the "currently-unowned architectural gap" flagged in
  Packages 011-014's own reports.
- A future package could resolve `PlanStatus.READY` (a validated Plan
  a Dispatcher has accepted for execution) and `PlanStatus.COMPLETED`
  (all steps' underlying dispatch calls succeeded), reporting outcomes
  back onto the originating Plan.
- A future package could add plan optimization (redundant-step
  detection, step reordering for efficiency) or scheduling (deferred/
  recurring plan execution) - both explicitly out of this package's
  scope per its own Architectural Guidance.

---

## Release Rules

Per the Founder's explicit instruction: no commit, tag, or push was
performed. `CORE_SERVICES_VERSION` was not changed. This package is
not reported as complete or released - implementation ends after
successful local verification; final validation, integration, release,
version update, commit, and tag are the Founder's responsibility
against the live repository.
