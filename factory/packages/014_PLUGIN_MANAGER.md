# Implementation Package 014 - Plugin Manager

## Objective

Give ArgusOS a central mechanism for extending itself without
modifying the core application. Version 1 focuses on plugin
discovery, registration, lifecycle, and metadata; plugins are not
required to execute real business logic yet. Per the Founder's
Package 014 work order, the target architecture is:

```
Intent -> Capability Registry -> Intent Dispatcher -> Action -> Plugin Manager -> Workflow
```

extending Package 013's:

```
Intent -> Capability Registry -> Intent Dispatcher -> Action -> Workflow
```

---

## Specification Note

No `design/specifications/PLUGIN.md` exists in the repository - the
same situation as Packages 002, 009, 010, 011, 012, and 013. This
package is built directly from the Founder's explicit work order.

---

## Constraints (Explicit, Non-Negotiable)

- The Plugin Manager stores plugin metadata and lifecycle state only.
  It never executes a plugin, never dispatches intents, and never
  stores capability metadata itself - `argus/plugins/manager.py`'s
  only non-trivial logic is input *validation* at `register()` time
  and the `enabled`-flag replace at `enable()`/`disable()` time, not
  execution.
- `list_plugins()` and `list_exported_capabilities()` are pure
  enumerations: neither applies any enabled/disabled policy on either
  the `Plugin` or the `Capability` - verified by test
  (`tests/test_plugin_manager.py::ListPluginsTests::test_includes_disabled_plugins`,
  `ListExportedCapabilitiesTests::test_includes_capabilities_from_disabled_plugins`).
- `PluginManager` never imports `argus.capability.registry` and never
  calls `ICapabilityRegistry.register()` - the Capability Registry is
  not redesigned, and integration is one-directional (Plugin Manager
  exposes; a caller, `bootstrap.py` in Version 1, decides whether to
  act on what is exposed).

---

## Architectural Decisions

### 1. The target architecture's "Action -> Plugin Manager -> Workflow" positioning is not wired into the dispatch path in Version 1

The work order describes `PluginManager` entirely in terms of
discovery/registration/lifecycle/metadata ("It is NOT responsible for
dispatching intents or storing capability metadata," "Plugins are NOT
required to execute real business logic yet"). Nothing in the
Plugin Manager, Capability Integration, or Bootstrap sections asks for
any change to `argus/dispatcher/` or `argus/workflow/`, and the
Architectural Guidance section's separation-of-responsibilities list
does not mention the dispatch path touching plugins at all. The
diagram's placement of Plugin Manager between Action and Workflow is
therefore read as directional/aspirational for a future version, not
as a Version 1 requirement to intercept `IntentDispatcher.dispatch()`
or `Action.execute()`. Accordingly, `argus/dispatcher/action.py`,
`argus/dispatcher/dispatcher.py`, and `argus/workflow/` are untouched
by this package - confirmed by `git diff --stat` showing no changes
outside `argus/plugins/`, `argus/bootstrap.py`,
`argus/events/event_types.py`, and the test/documentation files listed
below.

### 2. `Plugin.exported_capabilities` holds live `Capability` objects, not capability ids

The work order's Capability Integration section says the Plugin
Manager "should expose those capabilities so they can later be
registered with the Capability Registry" - which requires exposing
something a caller can hand directly to
`ICapabilityRegistry.register()`. Since `Capability` is an immutable
frozen dataclass (Package 013), holding direct references carries no
aliasing/mutation risk, so `Plugin.exported_capabilities:
Sequence[Capability]` stores the objects themselves rather than a
level of indirection (ids) that would force every caller to also hold
a `CapabilityRegistry`/lookup table just to resolve them back. This
creates a one-way, data-only dependency (`argus/plugins/` ->
`argus/capability/capability.py`) identical in shape to
`argus/dispatcher/action.py`'s existing data-only dependency on
`Capability` - never the reverse, and never a dependency on
`argus/capability/registry.py` itself.

### 3. Bootstrap wraps the same five Capability instances already registered with the Capability Registry, rather than constructing new ones

Per "Provide one or more built-in plugins representing the existing
workflow implementations" and "Behavior should remain unchanged,"
`bootstrap.py` builds one built-in `Plugin` ("Core Workflows") whose
`exported_capabilities` is
`tuple(capability_registry.list_capabilities())` - the identical
`Capability` objects already registered with the Capability Registry
in Package 013's population step, not copies. This means: (a) nothing
is registered twice with the Capability Registry (`PluginManager`
never calls into it), (b) `PluginManager.list_exported_capabilities()`
and `CapabilityRegistry.list_capabilities()` are verifiably
referencing the same objects (`tests/test_bootstrap.py::
BootstrapTests::test_bootstrap_plugin_manager_exports_same_capabilities_as_registry`
asserts `assertIs` on each), and (c) dispatcher/workflow behavior is
completely unaffected, satisfying "Behavior should remain unchanged"
literally rather than approximately.

### 4. `enable()`/`disable()` are unconditional, idempotent-in-effect registry operations, not IService lifecycle methods

Both methods always perform the replace-and-publish (via
`dataclasses.replace`, since `Plugin` is frozen) regardless of the
plugin's prior state - calling `enable()` on an already-enabled plugin
still succeeds and still publishes `PLUGIN_ENABLED`, rather than
silently no-op-ing. This was a deliberate simplicity choice per this
package's own "Keep the implementation simple" instruction: adding
conditional no-op detection was not asked for and would have added a
second code path (publish vs. don't) for no behavioral requirement
this package's work order specifies.

### 5. No new abstraction was introduced for "plugin discovery from disk"

The work order's own scope note - "Version 1 focuses on plugin
discovery, registration, lifecycle, and metadata" - is read alongside
"Plugins are NOT required to execute real business logic yet" as
meaning *registration-time* discovery (a caller constructs a `Plugin`
and calls `register()`), not filesystem/entry-point scanning. No
loader, no plugin-directory convention, and no dynamic import
machinery were added, per the Architectural Guidance's explicit
"Avoid introducing unnecessary abstraction" instruction - `bootstrap.py`
is, in Version 1, the sole place a `Plugin` is ever constructed.

---

## Events

Four new `EventType` members - `PLUGIN_REGISTERED`,
`PLUGIN_UNREGISTERED`, `PLUGIN_ENABLED`, `PLUGIN_DISABLED` - exactly
the four the work order names as examples, all judged genuinely
useful: the first two mirror `CapabilityRegistry`'s
`CAPABILITY_REGISTERED`/`CAPABILITY_UNREGISTERED` precedent (Package
013) for a metadata CRUD store, and the latter two are the natural
observable transitions for this package's two additional lifecycle
operations (`enable`/`disable`) that Capability Registry has no
equivalent of. All four are published on success only - never on a
failed/rejected call, per test
(`tests/test_plugin_manager.py::RegisterTests::test_failed_register_does_not_publish`
and equivalent tests for unregister/enable/disable).

No fifth event was added for "a plugin's capabilities were exposed":
`list_exported_capabilities()` is a pure read, with no state change
to report, matching `find_by_intent_type()`'s identical no-event
precedent (Package 013) - per this package's explicit "Only add
events that are genuinely useful" instruction.

---

## IService Adoption

`IPluginManager` does NOT inherit `IService` - a deliberate, documented
non-adoption, not an oversight, and the second consecutive one
following Capability Registry (013). `PluginManager` is
architecturally identical to Knowledge Service (006), Memory Service
(007), and Capability Registry (013): fully usable the instant it is
constructed, with nothing for `start()`/`stop()` to meaningfully gate.
`enable()`/`disable()` were explicitly considered and rejected as
IService-lifecycle candidates - they mutate an individual Plugin's
flag, not the manager's own runtime state, exactly like
`Scheduler.pause()`/`resume()` mutating an individual `ScheduledTask`
(Package 008) without implying anything about `Scheduler`'s own
lifecycle. See `argus/plugins/interfaces.py`'s Architectural Note and
`design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md`'s newly
appended Empirical Finding, which records this as the second
consecutive new *non*-adopter data point.

---

## Repository Verification Note

The uploaded repository ("ArgusOS (13).zip") passed pre-flight
verification on the first attempt - unlike the two prior packages,
which each required a Founder-corrected "...updated.zip" re-upload
after an initial `CORE_SERVICES_VERSION`-behind-tag mismatch was
reported. All four required checks passed directly: `argus/capability/`
(Package 013) present; HEAD (`6cc70f6`, "Synchronize repository
version with v0.1.3 release") confirmed a clean one-commit descendant
of tag `v0.1.3` (which itself points to `649ca09`, "Implement Package
013 Capability Registry") via `git merge-base --is-ancestor`, with
`git diff 649ca09..HEAD --stat` confirming the intervening commit
touches only `argus/bootstrap.py`, 1 insertion/1 deletion (a
version-only sync); `python -m pytest` passing (693 passed, 38
subtests) and `python main.py` starting and shutting down cleanly
(exit 0); `CORE_SERVICES_VERSION == "0.1.3"` confirmed at
`argus/bootstrap.py`. One filename-only observation, not a
verification failure: the work order's pre-flight step 1 names
"ArgusOS(13)updated.zip," while the actual upload was "ArgusOS
(13).zip" - immaterial, since the repository's actual content (commit
history, tag, version constant, test results) matched every
substantive requirement.

---

## Specifications Referenced

- factory/packages/013_CAPABILITY_REGISTRY.md (nearest precedent for a
  metadata-only registry that deliberately does not adopt `IService`,
  for its register/unregister/publish-on-success pattern, and for its
  one-way dependency discipline against `argus/dispatcher/`)
- factory/packages/008_SCHEDULER_SERVICE.md (precedent for
  ungated, registry-style per-item lifecycle operations - `pause()`/
  `resume()` - that do not imply anything about the owning service's
  own `IService` state, directly informing this package's
  `enable()`/`disable()` design)
- factory/packages/006_KNOWLEDGE_SERVICE.md (nearest precedent for
  create/delete event publication on a metadata CRUD store)

---

## Files Created

```
argus/
    plugins/
        __init__.py
        plugin.py
        manager.py
        interfaces.py
        exceptions.py
tests/
    test_plugin.py
    test_plugin_manager.py
```

## Files Modified

```
argus/bootstrap.py            (construct + register Plugin Manager as
                                14th core service, immediately after
                                Capability Registry; builds one
                                built-in "Core Workflows" Plugin
                                wrapping the same five Capability
                                instances already registered with the
                                Capability Registry; CORE_SERVICES_VERSION
                                left at "0.1.3" - not advanced)
argus/events/event_types.py   (4 new event types)
argus/tests/test_bootstrap.py (CORE_SERVICE_NAMES tuple only, per the
                                standing Package 011 rule)
tests/test_bootstrap.py       (CORE_SERVICE_NAMES tuple + 3 new tests)
design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md (Empirical Finding
                                appended; Status remains Proposed)
CHANGELOG.md, DEVLOG.md, IMPLEMENTATION_REPORT.md, factory/ROADMAP.md
```

`argus/dispatcher/`, `argus/capability/`, and `argus/workflow/` are
unchanged - per Architectural Decision 1 above, this package does not
wire the Plugin Manager into the dispatch path in Version 1.

---

## Test Totals

674 tests passing via `python -m unittest discover -s tests` (605 from
Packages 002-013, plus 19 new in `test_plugin.py`, plus 47 new in
`test_plugin_manager.py`, plus 3 net new in `test_bootstrap.py`).
`python -m unittest discover -s argus/tests` remains at 64 (duplicate
tree unaffected beyond the standing `CORE_SERVICE_NAMES` sync).
`python -m pytest` also passes: 762 passed, 38 subtests passed
(pytest's collection counts subtests differently than `unittest`'s
runner; both report zero failures).

---

## Coverage

100% line coverage on every new/modified module measured for this
package: `argus/plugins/__init__.py`, `argus/plugins/plugin.py`,
`argus/plugins/manager.py`, `argus/plugins/interfaces.py`,
`argus/plugins/exceptions.py`, `argus/bootstrap.py`, and
`argus/events/event_types.py` - all 100%, no accepted gaps. Overall
repository coverage: 99%, unchanged from Package 013 (the remaining
uncovered lines are pre-existing, out-of-scope for this package).

---

## Known Limitations

- Plugin discovery is registration-only in Version 1: there is no
  filesystem/entry-point scanning, no dynamic import machinery, and no
  plugin-directory convention. A caller (`bootstrap.py`) must
  construct and register every `Plugin` explicitly - by design, per
  this package's own Version 1 scope and the Architectural Guidance's
  "avoid introducing unnecessary abstraction" instruction.
- Plugins do not execute anything: there is no `Plugin.activate()`,
  no sandboxing, and no relationship between a `Plugin` and any
  `Action`/`WorkflowAction` beyond the `exported_capabilities` data
  link - matching the work order's explicit "Plugins are NOT required
  to execute real business logic yet."
- `list_exported_capabilities()`'s capabilities are not automatically
  registered with the Capability Registry. `PluginManager` only
  exposes them; a caller must decide whether and how to call
  `ICapabilityRegistry.register()` on any of them. In Version 1, the
  only caller (`bootstrap.py`) already registered these same five
  Capabilities directly in Package 013's population step, so no
  caller currently exercises this path for the built-in plugin.

---

## Release Rules

Per the Founder's explicit instruction: no commit, tag, or push was
performed. `CORE_SERVICES_VERSION` was not changed - it remains
`"0.1.3"`, matching the currently released version. This package is
not reported as complete or released - implementation ends after
successful local verification; final validation, integration, release,
version update, commit, and tag are the Founder's responsibility
against the live repository.
