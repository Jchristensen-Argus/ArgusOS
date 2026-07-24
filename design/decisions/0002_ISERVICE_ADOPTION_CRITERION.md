# ADR-0002: IService Adoption Criterion

## Status

Proposed

---

## Date

2026-07-24

---

## Context

Package 005 defined `IService` (`initialize`, `start`, `stop`, `status`) as
"the common lifecycle contract every ArgusOS service will implement," but
implemented no adopters. Separately, Package 005 also introduced
`LifecycleManager`, which tracks each service's `LifecycleState` centrally,
keyed by service name, independent of any object reference.

Package 004 had given `ServiceDescriptor` its own `state: ServiceState`
field. Once `LifecycleManager` existed, that became a second, unsynchronized
model of the same concept for the same five services - flagged as a known
limitation when Package 005 shipped, and eliminated in the Package 005
architectural revision by removing `state` from `ServiceDescriptor`
entirely. `LifecycleManager` is now the sole owner of runtime lifecycle
state for every service ArgusOS tracks.

`IService.status()` reintroduces the same shape of risk. Its signature is
`status(self) -> LifecycleState`, with no parameter for a `LifecycleManager`
or a service name - so any class that implements `IService` must track its
*own* internal `LifecycleState` in order to answer `status()` at all. If
that same service is also registered with `LifecycleManager` (as every
core service is, via `bootstrap.py`), there are once again two independent
variables representing "the current lifecycle state of this service": the
object's own internal state, and `LifecycleManager`'s entry for that
service's name. Nothing enforces that a call to `service.stop()` is always
paired with a call to `lifecycle_manager.stop(name)`; if the two are ever
called out of lockstep, the two records of "what state is this service in"
silently diverge.

This surfaced concretely during Package 007 (Memory Service). Memory
Service has no genuine multi-phase behavior in its current design (no
background thread, no connection to open or close - it is fully usable the
moment its constructor returns), so adopting `IService` for it would have
added the duplicate-state risk above purely for architectural symmetry,
with no corresponding behavioral need. `IService` adoption was deliberately
deferred; Memory Service is registered with `LifecycleManager` as
`LifecycleState.REGISTERED` only, exactly like the six core services before
it.

---

## Decision

Proposed criterion for every future ArgusOS service, core or otherwise:

**Adopt `IService` only when a service has genuine, distinct behavior at
each lifecycle phase** - specifically, when `start()` and `stop()` would do
real, distinct work (e.g., opening/closing a connection, starting/stopping
a background thread or timer loop, acquiring/releasing an external
resource) that cannot happen at construction time and must not happen
automatically.

Services that are fully functional the instant they are constructed, with
no meaningful "constructed but not yet started" state, should remain
`LifecycleManager`-`REGISTERED`-only, exactly like Configuration, the
Logger, the Event Bus, the Service Registry, the Lifecycle Manager itself,
the Knowledge Service, and the Memory Service today.

This is not (yet) a rule specific to "core services" versus "engines" - it
is a per-service judgment, applied the same way to any future package.
Candidates should be evaluated individually:

- **Scheduler**: a strong candidate for genuine adoption. Its own
  specification (`design/specifications/SCHEDULER.md`) names a "Timer
  Engine" among its internal components; if implemented with an actual
  background tick loop, `start()`/`stop()` would have real, distinct work
  to do.
- **Navigator**: plausible, for the same reason (`Queue Manager`, active
  task execution implies a real running/not-running distinction) - to be
  confirmed when Navigator is actually specified for implementation.
- **Atlas**: probably not, by default - its spec is CRUD/search-shaped,
  similar to Knowledge Service and Memory Service, unless its eventual
  design adds something with genuine startup behavior (e.g., warming a
  search index).
- **Cortex**: unknown - no specification file exists yet.

**Whichever service becomes ArgusOS's first genuine `IService` adopter
should also resolve the interface gap this ADR identifies**, not carry the
duplication forward silently. Two options for that future package to
weigh, not resolved by this ADR:

1. Revise `IService.status()` to require a `LifecycleManager` and the
   service's own registered name to be injected at construction, so
   `status()` can delegate to `lifecycle_manager.status(name)` instead of
   tracking a second, independent value.
2. Remove `status()` from `IService` entirely, treating `LifecycleManager`
   as the only place any caller ever asks "what state is this service in,"
   and leave `IService` as a pure behavioral contract (`initialize`,
   `start`, `stop`) with no state-reporting obligation of its own.

Either would eliminate the duplication at its root, the same way the
Package 005 revision did for `ServiceDescriptor`. Neither is adopted by
this ADR: `IService` is unchanged, and no service implements it yet.

---

## Consequences

Positive

- No ArgusOS service currently has two independent, potentially
  divergent records of its own lifecycle state.
- A clear, reusable per-service test ("does start()/stop() do real,
  distinct work?") for future package authors to apply, rather than a
  case-by-case guess.
- The interface gap in `IService.status()` is documented before any code
  depends on it, rather than being discovered after multiple services
  have already implemented it inconsistently.

Trade-offs

- `IService` remains unimplemented by anything as of Package 007 - the
  contract Package 005 defined is still unexercised in practice.
- The first real adopter inherits extra work: resolving the `status()`
  duplication question is now an explicit prerequisite, not something it
  can defer the way Memory Service did.
- This ADR proposes a criterion, not a mechanical rule; applying it still
  requires judgment about what counts as "genuine, distinct" phase
  behavior, which could be interpreted inconsistently by different future
  package authors without deliberate cross-checking against this document.

---

## Related Documents

- factory/packages/005_SERVICE_LIFECYCLE.md
- factory/packages/007_MEMORY_SERVICE.md (Out of Scope section)
- argus/lifecycle/interfaces.py (IService)
- argus/lifecycle/lifecycle.py (LifecycleManager)
- CHANGELOG.md, DEVLOG.md (Package 005 revision and Package 007 entries)

---

## Empirical Finding (Package 008 - Scheduler Service)

Scheduler is this ADR's proving ground, per the Founder's standing
instruction ("leave IService unchanged for now... use the first real
adopter... if the implementation confirms the duplication concern, we'll
revisit the interface in a dedicated architectural package").

**The concern is confirmed, empirically, not just theoretically.**
`tests/test_scheduler.py::IServiceLifecycleDivergenceTests` registers a
`Scheduler` with a real `LifecycleManager` exactly the way `bootstrap.py`
does (register-only), then calls `scheduler.initialize()` and
`scheduler.start()` directly - a realistic action, since nothing about
`IScheduler`'s public contract discourages a caller from doing exactly
this to make `tick()` usable. The result: `lifecycle_manager.status(
"scheduler")` still reports `LifecycleState.REGISTERED`, while
`scheduler.status()` reports `LifecycleState.RUNNING`. The two disagree,
with nothing in either class detecting or preventing it.

`bootstrap.py` itself does not trigger this - it registers Scheduler with
the Lifecycle Manager but never calls `scheduler.initialize()`/`start()`,
so the two remain consistent (`REGISTERED` / `CREATED`) for now. But that
consistency is a discipline `bootstrap.py`'s author has to maintain by
hand, not something the framework enforces. The first real caller that
needs `tick()` to work (necessarily calling `scheduler.initialize()` and
`scheduler.start()` on the object itself) will face this exact choice:
either also thread a `LifecycleManager` + service-name update through
every such call site, by convention, forever - or accept that the two
trackers can silently disagree.

**Recommendation:** per the Founder's own standing instruction, this
now qualifies as "confirmed" and warrants a dedicated architectural
package to resolve `IService`'s `status()` duplication, per one of the two
options already proposed above (inject `LifecycleManager` + name so
`status()` can delegate, or drop `status()` from `IService` entirely and
treat `LifecycleManager` as the only source of truth). This ADR's Status
remains `Proposed`, per instruction; only the Founder/Architect elevates it
to `Accepted` or opens the follow-up package.
