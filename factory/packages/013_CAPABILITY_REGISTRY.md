# Implementation Package 013 - Capability Registry

## Objective

Give ArgusOS a single source of truth describing everything it knows
how to do, and remove that same knowledge from the Intent Dispatcher,
which previously held it directly (Package 012's `register_mapping`/
`remove_mapping`/`list_mappings` surface). Per the Founder's Package
013 work order:

```
Intent -> Capability Registry -> Intent Dispatcher -> Action -> Workflow
```

replacing Package 012's:

```
Intent -> Intent Dispatcher -> Action -> Workflow
```

---

## Specification Note

No `design/specifications/CAPABILITY.md` exists in the repository -
the same situation as Packages 002, 009, 010, 011, and 012. This
package is built directly from the Founder's explicit work order.

---

## Constraints (Explicit, Non-Negotiable)

- The Capability Registry stores metadata only. It never executes
  workflows, never dispatches intents, and contains no business
  logic - `argus/capability/registry.py`'s only non-trivial logic is
  input *validation* at `register()` time, not execution.
- `find_by_intent_type()` is a pure filter: it applies no
  enabled/disabled policy and selects between multiple matches for
  nothing - that selection policy belongs to whoever resolves a
  Capability into something to execute (`IntentDispatcher.resolve()`
  in Version 1), verified by test
  (`tests/test_capability_registry.py::FindByIntentTypeTests::test_returns_disabled_capabilities_too`).
- The Intent Dispatcher no longer owns any capability knowledge of
  its own: as of this package, `IntentDispatcher` holds no internal
  `IntentType -> Action` mapping anywhere in its class. Every
  `dispatch()` call queries the injected `ICapabilityRegistry` live.

---

## Architectural Decisions

### 1. `IntentDispatcher` does not depend on `IWorkflowEngine`, even indirectly through the Capability Registry

`Capability` is pure data (a frozen dataclass: `name`, `description`,
`intent_types`, `action_kind`, `id`, `workflow_id`, `enabled`,
`metadata`) - it holds no live service reference, matching the
precedent set by every other value object in this codebase (`Workflow`,
`Intent`, `ConversationSession`). Something still has to translate a
Capability's metadata into an executable `Action`; that translation
lives in a new function, `argus.dispatcher.action.
build_action_from_capability(capability, *, workflow_engine)`, called
only via an injected `action_factory: Callable[[Capability], Action]`
- `IntentDispatcher.__init__` now takes `(event_bus,
capability_registry, action_factory)`, not `(event_bus,
workflow_engine)`. `bootstrap.py` builds the actual callable via
`functools.partial(build_action_from_capability,
workflow_engine=workflow_engine)`. This preserves Package 012's
hard-won zero-`argus.workflow`-dependency property in `dispatcher.py`
itself, verified by the same source-inspection technique Package 012
used (`tests/test_intent_dispatcher.py::WorkflowEngineDelegationTests::
test_dispatcher_never_imports_workflow_engine_module`).

### 2. `argus/capability/` has zero dependency on `argus/dispatcher/`

The dependency runs one direction only: `argus/dispatcher/` depends on
`argus/capability/` (for `Capability`, `ICapabilityRegistry`), never
the reverse. `CapabilityRegistry.register()`'s validation needs to
know that a `"workflow"`-kind capability requires a `workflow_id`, but
does this via a local string constant (`_WORKFLOW_ACTION_KIND =
"workflow"`, documented as matching `WorkflowAction.kind`'s value by
convention) rather than importing `WorkflowAction` itself - importing
it would have created a circular import
(`argus.capability.registry -> argus.dispatcher.action ->
argus.capability.capability`), since `build_action_from_capability`
(in `argus.dispatcher.action`) already imports `Capability`.

### 3. `IIntentDispatcher`'s public contract changed: `register_mapping`/`remove_mapping`/`list_mappings` removed; `resolve()`'s return type changed

Per "The Intent Dispatcher should no longer own knowledge of available
capabilities," `register_mapping()`, `remove_mapping()`, and
`list_mappings()` were removed from `IIntentDispatcher` entirely -
their responsibility moved to `ICapabilityRegistry.register()`/
`unregister()`/`list_capabilities()`, a genuinely different, better-
named home, not a renamed duplicate. `resolve(intent)` is kept (its
name maps directly onto the work order's own "Dispatcher
responsibilities become: resolve capability..." wording) but now
returns a `Capability`, not an `Action` - `IntentDispatcher.resolve()`
queries `ICapabilityRegistry.find_by_intent_type()` and applies a new,
explicit selection policy: the first *enabled* match, in the
registry's own registration order (documented in both
`resolve()`'s docstring and tested directly -
`tests/test_intent_dispatcher.py::ResolveTests`). This is a deliberate
breaking change to Package 012's public interface, explicitly
authorized by this package's "Modify Package 012 only where necessary"
instruction, since realizing the target architecture requires it.

### 4. `NoMappingError` renamed to `NoCapabilityError`; `DuplicateMappingError`/`MappingNotFoundError` removed from `argus/dispatcher/exceptions.py`

`DuplicateMappingError`/`MappingNotFoundError` no longer apply to
anything the dispatcher does (that responsibility, and its own
exceptions - `DuplicateCapabilityError`/`CapabilityNotFoundError` -
now live in `argus/capability/exceptions.py`). `NoMappingError` was
renamed to `NoCapabilityError` since "mapping" is no longer the
operative concept once `resolve()` returns a `Capability` -
`DispatcherError`, `InvalidIntentError`, `InvalidActionError`, and
`ActionExecutionError` are unchanged.

### 5. `Action` was NOT renamed

Considered, per this package's explicit "you MAY rename it... ONLY if
it meaningfully improves the architecture" allowance, and rejected:
`Action`'s one-method (`execute()`) contract is completely unaffected
by this refactor - only *where* an Action gets constructed changed
(via `build_action_from_capability`, called through an injected
factory, instead of `bootstrap.py` registering pre-built `Action`
instances directly via `register_mapping()`). A rename here would have
been cosmetic only, which this package's own instruction explicitly
rules out. See `argus/dispatcher/action.py`'s Non-Responsibilities for
this reasoning recorded in the source itself.

---

## Events

Two new `EventType` members, `CAPABILITY_REGISTERED` and
`CAPABILITY_UNREGISTERED`, mirror Knowledge Service's
`KNOWLEDGE_CREATED`/`KNOWLEDGE_DELETED` precedent (Package 006) for a
metadata CRUD store - published by `CapabilityRegistry.register()`/
`unregister()` on success only (never on a failed/rejected call, per
test:
`tests/test_capability_registry.py::RegisterTests::test_failed_register_does_not_publish`).

No new event was added for "a Capability was resolved" as a step
distinct from the existing `ActionResolved` event: `ActionResolved`'s
payload now additionally carries `capability_id` alongside
`action_kind`, folding capability resolution and Action construction
into the same event slot Package 012 already established, per this
package's explicit "Do not introduce unnecessary events" instruction.
The six dispatch events (`IntentDispatched`, `ActionResolved`,
`WorkflowSelected`, `DispatchStarted`, `DispatchCompleted`,
`DispatchFailed`) are otherwise unchanged from Package 012;
`DispatchFailed`'s `stage` payload field gained a new possible value,
`"build"` (an `action_factory` failure), alongside the existing
`"resolve"` and `"execute"`.

---

## IService Adoption

`ICapabilityRegistry` does NOT inherit `IService` - a deliberate,
documented non-adoption, not an oversight. `CapabilityRegistry` is
architecturally identical to Knowledge Service (006) and Memory
Service (007): fully usable the instant it is constructed, with
nothing for `start()`/`stop()` to meaningfully gate. See
`argus/capability/interfaces.py`'s Architectural Note and
`design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md`'s newly
appended Empirical Finding, which records this as the first new
*non*-adopter data point since Memory Service.

---

## Repository Verification Note

The first uploaded repository for this package failed pre-flight
verification: its tag (`v0.1.2`) confirmed Package 012 had been
integrated, committed, and released, but `argus/bootstrap.py`'s
`CORE_SERVICES_VERSION` constant still read `"0.1.1"` - the same
category of one-release-behind mismatch already seen before Package
012. Per this package's explicit "if any verification fails, STOP"
instruction, this was reported rather than worked around. The Founder
corrected the repository directly (commit `a440c77`, "Synchronize
repository version with v0.1.2 release") and supplied a corrected
upload. Pre-flight was re-run against that corrected repository and
passed: `CORE_SERVICES_VERSION == "0.1.2"` matching tag `v0.1.2` (HEAD
a clean one-commit descendant of it), `python -m pytest` passing (641
passed, 38 subtests), `python main.py` starting and shutting down
cleanly - all confirmed before any Package 013 code was written.

---

## Specifications Referenced

- factory/packages/012_INTENT_DISPATCHER.md (the interface this
  package revises)
- factory/packages/006_KNOWLEDGE_SERVICE.md (nearest precedent for a
  metadata CRUD core service that does not adopt `IService`, and for
  create/delete event publication on such a store)
- factory/packages/011_CONVERSATION_MANAGER.md (nearest precedent for
  "assume the referenced workflow_id may not be registered yet" -
  the same assumption this package's Version 1 population makes)

---

## Files Created

```
argus/
    capability/
        __init__.py
        capability.py
        exceptions.py
        interfaces.py
        registry.py
tests/
    test_capability.py
    test_capability_registry.py
```

## Files Modified

```
argus/dispatcher/
    __init__.py             (export surface updated)
    action.py                (+ build_action_from_capability)
    dispatcher.py             (constructor + resolve()/dispatch() rewritten)
    exceptions.py             (NoMappingError -> NoCapabilityError;
                                DuplicateMappingError/MappingNotFoundError removed)
    interfaces.py              (register_mapping/remove_mapping/list_mappings
                                 removed; resolve() now returns Capability)
argus/bootstrap.py            (construct + register Capability Registry as
                                13th core service; Intent Dispatcher now
                                14th, depends on it; CORE_SERVICES_VERSION
                                left at "0.1.2" - not advanced)
argus/events/event_types.py   (2 new event types)
argus/tests/test_bootstrap.py (CORE_SERVICE_NAMES tuple only, per the
                                standing Package 011 rule)
tests/test_bootstrap.py       (CORE_SERVICE_NAMES tuple + 3 new tests)
tests/test_dispatcher.py      (+ build_action_from_capability tests)
tests/test_intent_dispatcher.py (rewritten for the new IntentDispatcher
                                  constructor/resolve()/dispatch())
design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md (Empirical Finding
                                appended; Status remains Proposed)
CHANGELOG.md, DEVLOG.md, IMPLEMENTATION_REPORT.md, factory/ROADMAP.md
```

`argus/dispatcher/mapping.py` (`DEFAULT_WORKFLOW_IDS`) is unchanged -
reused as-is by `bootstrap.py` to build this package's five Version 1
Capabilities, per this package's own "Populate Version 1 using the
existing workflow mappings introduced in Package 012" requirement.

---

## Test Totals

605 tests passing (487 from Packages 002-011, minus 45 replaced by 38
in the rewritten `test_intent_dispatcher.py`, plus 4 new in
`test_dispatcher.py`, plus 52 new in `test_capability.py`/
`test_capability_registry.py`, plus 2 net new in `test_bootstrap.py`).
`python -m pytest` also passes: 693 passed, 38 subtests passed
(pytest's collection counts subtests differently than
`unittest`'s runner; both report zero failures).

---

## Release Rules

Per the Founder's explicit instruction: no commit, tag, or push was
performed. `CORE_SERVICES_VERSION` was not changed. This package is
not reported as complete or released - implementation ends after
successful local verification; final validation, integration, release,
version update, commit, and tag are the Founder's responsibility
against the live repository.
