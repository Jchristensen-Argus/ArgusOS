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

## Empirical Finding (Package 009 - Intent Router)

`IIntentRouter` also inherits `IService`, per the Founder's explicit
Package 009 work order, making `IntentRouter` a second real adopter.
It confirms a *different* facet of this ADR's concern than Scheduler
did.

Scheduler (Package 008) showed two things at once: the duplicate-state
risk is real, and `IService` *can* carry genuine behavior (`tick()`
is gated on `RUNNING`). IntentRouter isolates the first finding from
the second: it tracks its own `LifecycleState` the same way Scheduler
does, to satisfy `status()`, but none of `parse()`, `route()`, or
`register_handler()` are gated by that state in any way. Calling
`parse()` on a router that has never been started behaves identically
to calling it on one that has been started and stopped. `IService` is
implemented here purely to satisfy the interface requirement in the
work order, not because IntentRouter has any phased behavior for
`start()`/`stop()` to enable or disable.

This means the duplicate-state risk this ADR describes now applies to
a service with *no* compensating behavioral benefit from adopting
`IService` at all - for `IntentRouter`, the interface costs a second
source of truth for lifecycle state and buys nothing in return. This
sharpens, rather than changes, the original proposed criterion
("adopt `IService` only when `start()`/`stop()` would do real,
distinct work"): `IntentRouter` is close to a counterexample the
criterion would have screened out, had it been binding rather than
Proposed.

**Recommendation:** unchanged from the Package 008 finding above - this
adds a second, differently-shaped data point in favor of a dedicated
architectural package to resolve `IService.status()`'s duplication,
and now also in favor of that package deciding whether `IService`
adoption should require a genuine behavioral gate as a precondition,
not just a self-tracked state variable. This ADR's Status remains
`Proposed`, per standing instruction; only the Founder/Architect
elevates it to `Accepted` or opens the follow-up package.

## Empirical Finding (Package 010 - Workflow Engine)

`IWorkflowEngine` also inherits `IService`, per the Founder's explicit
Package 010 work order, making `WorkflowEngine` a third real adopter.
Unlike IntentRouter (Package 009), this finding *reinforces* Scheduler's
(Package 008) rather than complicating it further.

`WorkflowEngine.execute()` is genuinely gated on the engine's own
`LifecycleState`: it raises `WorkflowError` unless the engine's
self-tracked state is `RUNNING`, exactly mirroring
`Scheduler.tick()`'s gating on `RUNNING`. `register_workflow()`,
`cancel()`, and `get_workflow()` remain ungated registry operations,
again mirroring Scheduler's `schedule`/`cancel`/`pause`/`resume`. This
is the second of three `IService` adopters to date (Scheduler,
IntentRouter, WorkflowEngine) where the interface carries real,
distinct behavior rather than being satisfied only to meet an
interface requirement.

Combined with the Package 009 finding, the picture across all three
adopters is now: two (Scheduler, WorkflowEngine) use `IService` for a
genuine behavioral gate on their single "do the actual work" method;
one (IntentRouter) adopts it with no behavioral gate at all, purely
because the work order required `IIntentRouter(IService)`. This
continues to support the original proposed criterion ("adopt
`IService` only when `start()`/`stop()` would do real, distinct
work") as a good discriminator - it would have correctly retained
Scheduler and WorkflowEngine as good fits and flagged IntentRouter as
questionable, had it been binding.

The duplicate-state risk itself is unaffected by this finding - it is
still structurally present for `WorkflowEngine` exactly as it was
proven for `Scheduler` in Package 008 (self-tracked `LifecycleState`
vs. whatever a `LifecycleManager` tracks by name for the same
service), since nothing new was done here to resolve it. This finding
adds evidence about *when* `IService` adoption is well-motivated, not
about whether the duplication problem itself has been fixed.

**Recommendation:** unchanged - a dedicated architectural package to
resolve `IService.status()`'s duplication is still warranted. This
package's finding strengthens (rather than weakens) the case for that
future package encoding "requires a genuine behavioral gate" as an
explicit precondition for `IService` adoption, now backed by three
consistent data points instead of two. This ADR's Status remains
`Proposed`, per standing instruction; only the Founder/Architect
elevates it to `Accepted` or opens the follow-up package.

## Empirical Finding (Package 011 - Conversation Manager)

`IConversationManager` also inherits `IService`, per the Founder's
explicit Package 011 work order, making `ConversationManager` a
fourth real adopter. Like Scheduler (008) and WorkflowEngine (010),
this finding reinforces rather than complicates the picture:
`receive()` - the manager's single "do real work" method - is
genuinely gated on the manager's own `LifecycleState` being
`RUNNING`, raising `ConversationError` otherwise. `start_session()`,
`end_session()`, `history()`, and `active_session()` remain ungated
registry operations, matching the precedent from both prior gated
adopters.

Across all four adopters to date: three (Scheduler, WorkflowEngine,
ConversationManager) use `IService` for a genuine behavioral gate on
their single "do the actual work" method; one (IntentRouter) adopts it
with no behavioral gate, purely because its own work order required
`IIntentRouter(IService)`. The pattern is now well-established and
consistent: a 3-to-1 ratio across four independently-specified
packages continues to support the criterion originally proposed in
this ADR ("adopt `IService` only when `start()`/`stop()` would do
real, distinct work") as a reliable discriminator.

The duplicate-state risk itself remains unaffected by this finding -
`ConversationManager` has the same self-tracked `LifecycleState` vs.
`LifecycleManager`-tracked-by-name duplication as every other adopter,
since nothing new was done here to resolve it.

**Recommendation:** unchanged - a dedicated architectural package to
resolve `IService.status()`'s duplication is still warranted. Four
consistent data points (three gated, one not, and no adopter to date
has needed anything the proposed criterion wouldn't have correctly
predicted) make a strong case that whatever package eventually
addresses ADR-0002 should encode "requires a genuine behavioral gate"
as an explicit precondition for future `IService` adoption. This
ADR's Status remains `Proposed`, per standing instruction; only the
Founder/Architect elevates it to `Accepted` or opens the follow-up
package.

## Empirical Finding (Package 012 - Intent Dispatcher)

`IIntentDispatcher` also inherits `IService`, per the Founder's
explicit Package 012 work order, making `IntentDispatcher` a fifth
real adopter. Like Scheduler (008), WorkflowEngine (010), and
ConversationManager (011), this finding reinforces rather than
complicates the picture: `dispatch()` - the dispatcher's single "do
real work" method - is genuinely gated on the dispatcher's own
`LifecycleState` being `RUNNING`, raising `DispatcherError` otherwise.
`register_mapping()`, `remove_mapping()`, `resolve()`, and
`list_mappings()` remain ungated registry operations, matching the
precedent from all three prior gated adopters.

Across all five adopters to date: four (Scheduler, WorkflowEngine,
ConversationManager, IntentDispatcher) use `IService` for a genuine
behavioral gate on their single "do the actual work" method; one
(IntentRouter) adopts it with no behavioral gate, purely because its
own work order required `IIntentRouter(IService)`. The pattern is now
a 4-to-1 ratio across five independently-specified packages, continuing
to support the criterion originally proposed in this ADR ("adopt
`IService` only when `start()`/`stop()` would do real, distinct work")
as a reliable discriminator.

The duplicate-state risk itself remains unaffected by this finding -
`IntentDispatcher` has the same self-tracked `LifecycleState` vs.
`LifecycleManager`-tracked-by-name duplication as every other adopter,
since nothing new was done here to resolve it.

**Recommendation:** unchanged - a dedicated architectural package to
resolve `IService.status()`'s duplication is still warranted. Five
consistent data points (four gated, one not, and no adopter to date
has needed anything the proposed criterion wouldn't have correctly
predicted) make an even stronger case that whatever package eventually
addresses ADR-0002 should encode "requires a genuine behavioral gate"
as an explicit precondition for future `IService` adoption. This
ADR's Status remains `Proposed`, per standing instruction; only the
Founder/Architect elevates it to `Accepted` or opens the follow-up
package.

## Empirical Finding (Package 013 - Capability Registry)

`ICapabilityRegistry`, per the Founder's Package 013 work order, does
NOT inherit `IService` - the first new core service since Memory
Service (Package 007) to deliberately abstain from adopting it.
`CapabilityRegistry` is a pure metadata CRUD store: `register`,
`unregister`, `get`, `find_by_intent_type`, `list_capabilities`, and
`contains` are all fully usable the instant the registry is
constructed, with no background thread, no connection to open or
close, and nothing for `start()`/`stop()` to meaningfully enable or
disable - architecturally identical to Knowledge Service (006) and
Memory Service (007).

This is a different kind of data point than any adopter recorded so
far: not a new adopter reinforcing the gated/ungated split, but a
new *non*-adopter correctly predicted by the criterion itself.
Applying "adopt `IService` only when `start()`/`stop()` would do
real, distinct work" to `CapabilityRegistry` during its design
correctly ruled out adoption before any code was written, the same
judgment call Memory Service's own report made for itself in Package
007. Eight core services now exist that do not implement `IService`
(Configuration, the Logger, the Event Bus, the Service Registry, the
Lifecycle Manager, Knowledge Service, Memory Service, and now
Capability Registry), alongside five that do (Scheduler, IntentRouter,
WorkflowEngine, ConversationManager, and IntentDispatcher - four of
which are genuinely gated).

**Recommendation:** unchanged - a dedicated architectural package to
resolve `IService.status()`'s duplication is still warranted for the
five existing adopters. This finding does not add urgency to that
recommendation, but it does reinforce that the criterion itself is
doing real work as a design-time filter, not just a post-hoc
classification exercise applied to packages that already adopted
`IService` regardless. This ADR's Status remains `Proposed`, per
standing instruction; only the Founder/Architect elevates it to
`Accepted` or opens the follow-up package.

## Empirical Finding (Package 014 - Plugin Manager)

`IPluginManager`, per the Founder's Package 014 work order, does NOT
inherit `IService` - the second consecutive new core service,
following Capability Registry (Package 013), to deliberately abstain
from adopting it. `PluginManager` is a pure metadata-and-lifecycle
CRUD store: `register`, `unregister`, `enable`, `disable`, `get`,
`list_plugins`, `list_exported_capabilities`, and `contains` are all
fully usable the instant the manager is constructed, with no
background thread, no connection to open or close, and nothing for
`start()`/`stop()` to meaningfully enable or disable - architecturally
identical to Knowledge Service (006), Memory Service (007), and
Capability Registry (013).

`enable()`/`disable()` are worth calling out explicitly, since their
names could be mistaken for lifecycle-phase behavior: they toggle the
`enabled` flag on an individual, already-registered `Plugin` - a
registry-style mutation of data the manager owns, exactly like
`Scheduler.pause()`/`resume()` toggling an individual `ScheduledTask`'s
state (Package 008) without implying anything about `Scheduler`'s own
`IService` lifecycle. They are not gated by, and do not participate
in, `PluginManager`'s own (nonexistent) lifecycle state. Version 1
plugins are also not required to execute real business logic (per
this package's own Objective), so there is no "active work" phase for
`start()`/`stop()` to gate even in principle - a stronger case for
non-adoption than Capability Registry's, which at least had no
lifecycle-shaped method names to potentially confuse the question.

This is now two consecutive new-service non-adoptions, both correctly
predicted by the criterion during design rather than discovered after
the fact. Nine core services now exist that do not implement
`IService` (Configuration, the Logger, the Event Bus, the Service
Registry, the Lifecycle Manager, Knowledge Service, Memory Service,
Capability Registry, and now Plugin Manager), alongside five that do
(Scheduler, IntentRouter, WorkflowEngine, ConversationManager, and
IntentDispatcher - four of which are genuinely gated).

**Recommendation:** unchanged - a dedicated architectural package to
resolve `IService.status()`'s duplication is still warranted for the
five existing adopters. Two consecutive non-adoptions strengthen the
observation from Package 013's finding that the criterion is doing
real design-time filtering work, and additionally show it correctly
handling a case (`enable`/`disable`) where lifecycle-sounding method
names could otherwise have prompted an unwarranted `IService` adoption
by pattern-matching on naming alone rather than on actual phased
behavior. This ADR's Status remains `Proposed`, per standing
instruction; only the Founder/Architect elevates it to `Accepted` or
opens the follow-up package.

## Empirical Finding (Package 015 - Planner)

`IPlanner`, per the Founder's Package 015 work order, does NOT
inherit `IService` - the third consecutive new core service, following
Capability Registry (013) and Plugin Manager (014), to deliberately
abstain from adopting it. `Planner` is a pure reasoning-only store:
`create_plan`, `add_step`, `remove_step`, `reorder_steps`,
`validate_plan`, `get_plan`, and `list_plans` are all fully usable the
instant the Planner is constructed, with no background thread, no
connection to open or close, and nothing for `start()`/`stop()` to
meaningfully enable or disable - architecturally identical to
Knowledge Service (006), Memory Service (007), Capability Registry
(013), and Plugin Manager (014).

This package sharpens the criterion's discriminating power one step
further than Package 014's finding did. Planner's methods are not
just individually stateless in the way Capability Registry's are -
`validate_plan()` performs the closest thing to "real work" of any
non-adopter so far (a Capability Registry lookup and a status
transition), yet it remains a single, synchronous, fully-available-
at-construction-time operation with no phase distinct from any other
method call. Nothing about it resembles `Scheduler.tick()`'s or
`WorkflowEngine.execute()`'s gate on the owning service's own
`RUNNING` state - there is no "Planner must be started before
validate_plan() will work" precondition anywhere in this design, nor
could there sensibly be one, since the work order's own Objective
("It performs reasoning only") rules out anything resembling a
background process by construction, not just by current
implementation choice.

Three consecutive new-service non-adoptions are now on record, each
correctly predicted by the criterion during design rather than
discovered after the fact. Ten core services now exist that do not
implement `IService` (Configuration, the Logger, the Event Bus, the
Service Registry, the Lifecycle Manager, Knowledge Service, Memory
Service, Capability Registry, Plugin Manager, and now Planner),
alongside five that do (Scheduler, IntentRouter, WorkflowEngine,
ConversationManager, and IntentDispatcher - four of which are
genuinely gated).

**Recommendation:** unchanged - a dedicated architectural package to
resolve `IService.status()`'s duplication is still warranted for the
five existing adopters. Three consecutive non-adoptions - twice the
length of the current adopter-side gated/ungated pattern's own
longest unbroken streak - make it increasingly clear that ArgusOS's
architecture is naturally splitting into two durable categories:
metadata/reasoning stores (now the majority of core services) and a
small, stable set of genuinely phased engines identified early
(Scheduler, WorkflowEngine, ConversationManager, IntentDispatcher).
This ADR's Status remains `Proposed`, per standing instruction; only
the Founder/Architect elevates it to `Accepted` or opens the
follow-up package.

## Empirical Finding (Package 016 - Agent Runtime)

`IAgentRuntime`, per the Founder's Package 016 work order, DOES inherit
`IService` - breaking the three-consecutive-non-adopter streak set by
Capability Registry (013), Plugin Manager (014), and Planner (015).
`AgentRuntime.start_execution()` and `resume_execution()` - the only
two methods that actually dispatch a PlanStep through the injected
`IIntentDispatcher` - are genuinely gated on the Runtime's own
lifecycle state being `RUNNING`, raising `InvalidExecutionStateError`
otherwise. `pause_execution()`, `cancel_execution()`, `get_execution()`,
and `list_executions()` remain ungated registry-style operations on
individual Executions, exactly mirroring `Scheduler.pause()`/`resume()`'s
(Package 008) and every metadata/reasoning registry's own lookup
methods in this codebase - none of which are affected by the owning
service's `IService` lifecycle.

This package is architecturally distinct from the three immediately
preceding non-adopters in a way the criterion itself predicts
correctly: Capability Registry, Plugin Manager, and Planner are all
metadata/reasoning stores with no "active work" phase even in
principle, whereas `AgentRuntime`'s entire purpose - "The Runtime owns
execution only" - is to perform genuine, effectful work
(dispatching through the Dispatcher, which in turn may run a
Workflow) that must not happen automatically at construction time and
should not be callable before the Runtime is deliberately started.
This is architecturally identical to `WorkflowEngine.execute()`
(Package 010), `ConversationManager.receive()` (Package 011), and
`IntentDispatcher.dispatch()` (Package 012) - all three genuinely
gated for the same reason.

Six adopters now exist (Scheduler, IntentRouter, WorkflowEngine,
ConversationManager, IntentDispatcher, and now AgentRuntime), five of
which are genuinely gated (all but IntentRouter). Ten core services
exist that do not implement `IService` (Configuration, the Logger,
the Event Bus, the Service Registry, the Lifecycle Manager, Knowledge
Service, Memory Service, Capability Registry, Plugin Manager, and
Planner).

**Recommendation:** unchanged - a dedicated architectural package to
resolve `IService.status()`'s duplication is still warranted, now for
six adopters rather than five. This package's finding is the clearest
demonstration yet that the criterion discriminates correctly in both
directions: it does not merely rubber-stamp non-adoption by default,
and it correctly identifies a new genuine adopter the moment a
package's actual purpose (executing real, effectful work through an
existing gated engine) calls for one - even immediately following
three consecutive packages that did not qualify. This ADR's Status
remains `Proposed`, per standing instruction; only the Founder/Architect
elevates it to `Accepted` or opens the follow-up package.
