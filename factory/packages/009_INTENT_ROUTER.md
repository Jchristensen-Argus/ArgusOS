# Implementation Package 009 - Intent Router

## Objective

Give ArgusOS a deterministic, rule-based way to turn raw text into a
structured `Intent` and route it to interested services exclusively
through the Event Bus, per the Founder's Package 009 work order.

---

## Specification Note

No `design/specifications/INTENT_ROUTER.md` exists in the repository
(unlike Scheduler, Memory, and Knowledge, each of which had a spec
file to implement against). This package is built directly from the
Founder's explicit, fully-detailed Package 009 work order instead -
the same situation as Package 002 (Bootstrap), which also had no
prior spec file. No architecture was invented to fill this gap: every
structural choice below traces to an explicit line in the Founder's
work order or to an established precedent from Packages 002-008.

---

## Constraints (Explicit, Non-Negotiable)

- Deterministic routing only. No AI, no machine learning, no external
  libraries, no regex-heavy heuristics - `argus/intent/parser.py` is
  fixed keyword lists and fixed precedence, in pure Python.
- Routing must not directly invoke services. `route()`'s only
  mechanism is `IEventBus.publish()`; `register_handler()` is sugar
  over `IEventBus.subscribe()`, not a second dispatch path. See
  `router.py`'s module docstring for the full reasoning.
- Unknown or unrecognized input must always produce a valid `Intent`
  with `name=IntentType.UNKNOWN`, never an exception. `parse()` raises
  only for genuinely non-string input.

---

## IService Adoption

`IIntentRouter` inherits `IService`, per the Founder's explicit
instruction. Unlike Scheduler (Package 008), where `tick()` is
genuinely gated on the `RUNNING` state, none of `parse()` / `route()`
/ `register_handler()` are gated by `IntentRouter`'s lifecycle state -
there is no background execution here for `start()`/`stop()` to
meaningfully enable or disable. `IntentRouter` still tracks its own
`LifecycleState` to satisfy `status()`, for consistency with
Scheduler's precedent and because the Founder's work order requires
`IIntentRouter(IService)`.

This makes `IntentRouter` a second, distinctly-shaped data point for
ADR-0002 (design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md):
Scheduler proved the duplicate-state risk is real *and* that `IService`
can gate genuine behavior; IntentRouter proves `IService` can also be
adopted with no behavioral gate at all, purely to satisfy an interface
requirement. Per the Founder's standing instruction, ADR-0002 remains
`Proposed` and `IService` itself is left unchanged; this finding is
appended to ADR-0002, not used to revise it. See
IMPLEMENTATION_REPORT.md's ADR Recommendation section.

---

## Specifications Referenced

- factory/packages/005_SERVICE_LIFECYCLE.md (`IService`, `LifecycleManager`)
- factory/packages/008_SCHEDULER_SERVICE.md (nearest precedent: an
  `IService`-inheriting core service with its own self-tracked state)
- design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md
- design/specifications/INTERFACES.md
- factory/standards/CODING_STANDARD.md

---

## Files to Create

argus/intent/
    __init__.py
    interfaces.py
    intent.py
    parser.py
    router.py
    exceptions.py

tests/
    test_intent.py
    test_intent_parser.py
    test_intent_router.py

---

## Files to Modify

- argus/bootstrap.py (construct and register `IntentRouter` as the
  ninth core service; bump `CORE_SERVICES_VERSION` to `"0.0.9"`)
- argus/events/event_types.py (add `INTENT_PARSED`, `INTENT_ROUTED`,
  `INTENT_FAILED`)
- tests/test_bootstrap.py (extend core-service assertions to nine
  services)
- CHANGELOG.md, DEVLOG.md

`design/ARCHITECTURE.md` is not modified by this package:
`IIntentRouter` inheriting `IService` is not a new architectural
decision (Scheduler already established the pattern in Package 008),
and no other architectural document requires updating for this
package's scope.

---

## Acceptance Criteria

- `python main.py` starts and shuts down cleanly.
- All pre-existing tests continue to pass.
- `IntentRouter` resolves from the Container and appears in the
  Service Registry and Lifecycle Manager (`LifecycleState.REGISTERED`),
  alongside the eight existing core services - registered only, not
  started, per the pattern established for every core service to date.
- `parse(text)` classifies the four given examples correctly
  ("Remember my dentist appointment" -> MEMORY, "Remind me tomorrow"
  -> SCHEDULE, "What is corrugated board?" -> QUESTION, "Shutdown
  Argus" -> COMMAND) and never raises for any string input, including
  empty or whitespace-only text (-> UNKNOWN).
- `parse()` raises `IntentParseError` for non-string input; `route()`
  raises `InvalidIntentError` for non-`Intent` input;
  `register_handler()` raises `InvalidIntentError` for a non-
  `IntentType` name or non-callable handler, and `DuplicateHandlerError`
  for an exact `(intent_name, handler)` pair registered twice.
- `route()`'s only invocation mechanism is `IEventBus.publish()`; a
  handler registered via `register_handler()` is only ever invoked as
  a downstream Event Bus subscriber, never called directly by
  `route()`.
- A handler's exception is caught and isolated (published as
  `IntentFailed`), never propagated out of `route()`, and never
  prevents other handlers for the same event from running.
- `IntentParsed` fires on every `parse()` call including UNKNOWN
  results; `IntentRouted` fires on every successful `route()` call;
  `IntentFailed` fires for router-level input failures (`parse()`/
  `route()` raising) and for isolated per-handler failures.

---

## Out of Scope

- Any AI/ML-based or regex-heavy classification.
- Direct invocation of any named service (Knowledge, Memory,
  Scheduler) from `IntentRouter`.
- Lifecycle-state gating of `parse()`/`route()`/`register_handler()`.
- Multi-language or locale-aware parsing.
- Confidence scores beyond the three fixed constants (1.0 / 0.6 / 0.0).
- Resolving the `IService` duplication question itself - this
  package's role is to add a second empirical data point, per the
  Founder's standing instruction, not to revise `IService`.
