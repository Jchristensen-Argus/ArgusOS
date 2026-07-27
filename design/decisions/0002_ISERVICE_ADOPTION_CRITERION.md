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

## Empirical Finding (Package 017 - Connector Framework)

`IConnectorManager`, per the Founder's Package 017 work order, DOES
inherit `IService` - continuing the pattern set by `AgentRuntime`
(Package 016) rather than the three-consecutive-non-adopter streak
that preceded it (Capability Registry - 013, Plugin Manager - 014,
Planner - 015). `ConnectorManager.invoke()` - the only method that
actually reaches out to an external system's connector implementation
(calling `connect()` then `invoke()` on it) - is genuinely gated on
the manager's own lifecycle state being `RUNNING`, raising
`InvalidConnectorStateError` otherwise. `register_connector()`,
`unregister_connector()`, `get_connector()`, `list_connectors()`,
`enable_connector()`, and `disable_connector()` remain ungated
registry-style operations on individual Connectors, exactly mirroring
`AgentRuntime`'s own pause/cancel/get/list precedent (Package 016) and
every other metadata/reasoning registry's lookup methods in this
codebase.

The reasoning is the direct analogue of Package 016's: `invoke()` is
"real, distinct work" in exactly the sense ADR-0002's criterion asks
about - it is the single point through which ArgusOS reaches an
external system (even a mocked one in Version 1), a strictly stronger
case for gating than `IntentDispatcher.dispatch()` (which merely
resolves and runs an internal Workflow) or `AgentRuntime.
start_execution()` (which merely dispatches Intents). Not gating
`invoke()` would let a caller invoke a connector before the framework
was deliberately started, with no guardrail at all standing between
"the object was constructed" and "an external call went out" - the
same risk the criterion was written to catch.

Seven adopters now exist (Scheduler, IntentRouter, WorkflowEngine,
ConversationManager, IntentDispatcher, AgentRuntime, and now
ConnectorManager), six of which are genuinely gated (all but
IntentRouter). Ten core services exist that do not implement
`IService` (Configuration, the Logger, the Event Bus, the Service
Registry, the Lifecycle Manager, Knowledge Service, Memory Service,
Capability Registry, Plugin Manager, and Planner).

**Recommendation:** unchanged - a dedicated architectural package to
resolve `IService.status()`'s duplication is still warranted, now for
seven adopters rather than six. This package's finding reinforces
Package 016's: the criterion continues to discriminate correctly,
identifying a genuine adopter precisely where a package's actual
purpose involves an effectful, gate-worthy operation, and continuing
to withhold adoption from packages that are pure metadata/reasoning
stores. This ADR's Status remains `Proposed`, per standing
instruction; only the Founder/Architect elevates it to `Accepted` or
opens the follow-up package.

## Empirical Finding (Package 018 - Knowledge Graph)

`IKnowledgeGraph`, per the Founder's Package 018 work order, DOES
inherit `IService` - but this package's finding is qualitatively
different from every prior one recorded here. Every previous adoption
or non-adoption decision (Packages 008-017) was this Engineer's own
judgment call, applying ADR-0002's proposed criterion to a work order
that left the question open. Package 018's work order does not leave
it open: it states plainly, "Create: `IKnowledgeGraph` - Extend
`IService`." Adoption itself was not a decision this Engineer made.

Applying the criterion independently to this package's actual methods,
however, would not have suggested adoption. `add_entity`,
`remove_entity`, `get_entity`, `list_entities`, `add_relationship`,
`remove_relationship`, `list_relationships`, `neighbors`, and
`find_by_type` are all synchronous, in-memory data operations with no
external call, no dispatch, and no phase distinction any of them could
plausibly be gated on - the Objective states plainly, "It is an
in-memory semantic graph... No graph algorithms yet... Only
foundational graph operations." This is architecturally much closer to
Capability Registry (013), Plugin Manager (014), and Planner (015) -
three deliberate non-adopters - than to Agent Runtime (016) or
Connector Manager (017), whose defining gated methods
(`start_execution()`, `invoke()`) each reach into dispatch or external
communication. No method on `KnowledgeGraph` was gated, since none
plausibly could be without inventing a "queries only work when
RUNNING" policy the work order never asked for (and one that would
sit awkwardly next to "The Planner may consult the Knowledge Graph,"
given bootstrap.py's standing "register only, never start" rule for
every core service - a Planner consultation should not spuriously fail
merely because nobody remembered to `start()` the graph).
`KnowledgeGraph` therefore implements the full IService lifecycle
boilerplate (`initialize()`/`start()`/`stop()`/`status()`) but gates
none of its own domain methods - exactly mirroring `IntentRouter`'s
(Package 009) identical shape, making `KnowledgeGraph` the **second**
IService adopter in this codebase with zero gated methods.

Eight adopters now exist (Scheduler, IntentRouter, WorkflowEngine,
ConversationManager, IntentDispatcher, AgentRuntime, ConnectorManager,
and now KnowledgeGraph), six of which are genuinely gated (all but
IntentRouter and KnowledgeGraph). Ten core services exist that do not
implement `IService` at all (Configuration, the Logger, the Event Bus,
the Service Registry, the Lifecycle Manager, Knowledge Service, Memory
Service, Capability Registry, Plugin Manager, and Planner).

**Recommendation:** unchanged in substance, with one addition worth
flagging explicitly. A dedicated architectural package to resolve
`IService.status()`'s duplication is still warranted, now for eight
adopters rather than seven. But this package's finding surfaces a new
question the criterion itself does not yet address: what should
happen when an explicit Founder instruction to adopt `IService`
diverges from what the criterion would independently conclude? This
Engineer's approach here was to follow the explicit instruction
faithfully (adoption is not this Engineer's call to make) while
applying the criterion's own logic to the *narrower* question left
open - which, if any, specific methods should be gated - and
concluding "none," consistent with `IntentRouter`'s established
precedent for exactly this shape of adopter. Whether ADR-0002 should
be revised to explicitly acknowledge "IService adoption may also be
directed rather than derived, in which case the criterion still
governs gating" is a question for the Founder/Architect, not something
this Engineer has resolved unilaterally. This ADR's Status remains
`Proposed`, per standing instruction; only the Founder/Architect
elevates it to `Accepted` or opens the follow-up package.

## Empirical Finding (Package 019 - Memory Integration)

`IMemoryIntegration`, per the Founder's Package 019 work order, DOES
inherit `IService` - again an explicit instruction, not this
Engineer's own judgment call, continuing the new category of finding
Package 018 introduced. Unlike Package 018's Knowledge Graph, however,
applying ADR-0002's criterion independently to this package's actual
methods *would also* have suggested adoption on its own -
`synchronize_memory()`, `synchronize_all()`, and `remove_memory()`
each perform genuine, effectful cross-system coordination: reading a
record from `IMemoryService` and writing an Entity (and its
Relationships) to `IKnowledgeGraph`, in the same call. This is
architecturally much closer to `AgentRuntime.start_execution()`
(Package 016) and `ConnectorManager.invoke()` (Package 017) - both
genuinely gated - than to `KnowledgeGraph`'s own purely in-memory,
single-system operations (Package 018), which is precisely why
`KnowledgeGraph` gated nothing while `MemoryIntegration` gates three
of its five methods. `synchronization_status()` and `reset()` remain
ungated - both are pure operations over `MemoryIntegration`'s own
internal bookkeeping only ("It owns no data itself"), never touching
either `IMemoryService` or `IKnowledgeGraph`, matching
`Scheduler.pause()`/`resume()`'s (Package 008) and every other
ungated registry-style operation in this codebase.

This package's finding directly resolves the open question Package
018's finding raised, in the opposite direction: there, an explicit
instruction and the criterion's own independent conclusion diverged
(the criterion alone would not have suggested adoption). Here, they
converge (the criterion alone *would* have suggested adoption,
independent of the explicit instruction). Taken together, Packages
018 and 019 give ADR-0002 its first paired evidence that "directed"
(Founder-instructed) and "derived" (criterion-applied) IService
adoption are genuinely separate questions that can agree or disagree
in either package - the explicit instruction settles *whether* a
class implements `IService`, while the criterion, applied
independently and afterward by this Engineer, still correctly governs
*which specific methods* are gated, regardless of which of the two
routes led to inheriting `IService` in the first place.

A distinct, unrelated naming issue also surfaced in this package,
worth recording separately from the adoption question itself: this
package's work order lists `status()` as one of `MemoryIntegration`'s
five domain Responsibilities, but `IService.status()` is already a
fixed abstract method returning `LifecycleState`, used identically by
every other adopter in this codebase. A method cannot satisfy both
contracts under one name without breaking Liskov substitution for any
caller treating `MemoryIntegration` polymorphically as an `IService`.
Resolved by naming the domain method `synchronization_status()`
instead, preserving `status()` exclusively for lifecycle reporting
everywhere in this codebase, with no exception - see
`argus/memory_integration/interfaces.py`'s own Architectural Note for
the full reasoning. This is a naming-collision resolution, not an
adoption-criterion question, and does not itself bear on ADR-0002 -
recorded here only because it was discovered in the course of this
same package's IService integration work.

Nine adopters now exist (Scheduler, IntentRouter, WorkflowEngine,
ConversationManager, IntentDispatcher, AgentRuntime, ConnectorManager,
KnowledgeGraph, and now MemoryIntegration), seven of which are
genuinely gated (all but IntentRouter and KnowledgeGraph). Ten core
services exist that do not implement `IService` at all (Configuration,
the Logger, the Event Bus, the Service Registry, the Lifecycle
Manager, Knowledge Service, Memory Service, Capability Registry,
Plugin Manager, and Planner).

**Recommendation:** unchanged in substance. A dedicated architectural
package to resolve `IService.status()`'s duplication is still
warranted, now for nine adopters rather than eight. This package's
finding, read alongside Package 018's, suggests ADR-0002 could
usefully be revised to formally separate "adoption" (whether a class
implements `IService` - which may be directed or derived) from
"gating" (which specific methods are gated on `RUNNING` - which
remains this Engineer's own criterion-driven judgment call regardless
of how adoption was decided), rather than treating the two as a single
combined decision as the ADR's current text implicitly does. This ADR's
Status remains `Proposed`, per standing instruction; only the
Founder/Architect elevates it to `Accepted`, revises its text, or opens
the follow-up package.

## Empirical Finding (Package 020 - Reasoning Engine)

`IReasoningEngine`, per the Founder's Package 020 work order, DOES
inherit `IService` - again an explicit instruction, not this
Engineer's own judgment call. Applying ADR-0002's criterion
independently to this package's actual methods, however, would NOT
have suggested adoption on its own - the same divergence Package 018's
Knowledge Graph exhibited, and the direct opposite of Package 019's
Memory Integration, where explicit instruction and the criterion's own
conclusion agreed. All six public methods (`query()`, `neighbors()`,
`find_paths()`, `related_entities()`, `entity_summary()`,
`relationship_summary()`) are synchronous, read-only, in-memory
operations over an already-injected `IKnowledgeGraph` (and, for
metadata enrichment only, `IMemoryIntegration.synchronization_status()`
- itself already ungated) - no external call, no dispatch, no write,
and no phase distinction any of them could plausibly be gated on. "It
does not make decisions. It does not execute plans. It performs
deterministic reasoning only," per this package's own Objective. This
is architecturally much closer to `KnowledgeGraph` (Package 018) and
`IntentRouter` (Package 009) - both zero-gated adopters - than to
`MemoryIntegration` (Package 019), `AgentRuntime` (Package 016), or
`ConnectorManager` (Package 017), whose genuinely gated methods each
perform effectful, stateful cross-system coordination or external I/O
that reading an already-populated, in-memory graph does not.
`ReasoningEngine` therefore implements the full IService lifecycle
boilerplate (`initialize()`/`start()`/`stop()`/`status()`) but gates
none of its own six public methods - exactly mirroring `KnowledgeGraph`'s
(Package 018) and `IntentRouter`'s (Package 009) identical shape,
making `ReasoningEngine` the **third** IService adopter in this
codebase with zero gated methods.

This package's finding also directly answers the question Package
019's finding raised about separating "adoption" from "gating" as
formally distinct questions - not by revising the ADR's text (still
not this Engineer's call), but by supplying a second real data point
for the divergent case: Packages 018 and 020 both show an explicit
"Extend IService" instruction paired with a criterion that
independently concludes "gate nothing," while Package 019 shows the
same explicit-instruction shape paired with a criterion that
independently concludes "gate the effectful methods." Directed
adoption (whether a class implements `IService`) and derived gating
(which specific methods are gated on `RUNNING`) continue to behave as
genuinely separable questions across four consecutive explicitly-
directed adopters (018, 019, 020, and - by extension - any future
package that states "Extend IService" outright): the instruction
settles the first question; this Engineer's own application of
ADR-0002's criterion, unchanged by which route led to `IService`
inheritance, continues to settle the second.

A distinct, unrelated design point also surfaced in this package,
worth recording separately from the adoption question itself: this
package's own Bootstrap section lists Memory Integration as a
dependency alongside Knowledge Graph, and its Objective states the
Reasoning Engine "consumes information from... Memory Integration" -
stronger language than Package 018's own "the Planner *may* consult
the Knowledge Graph" (a future capability, deliberately left
unexercised at the time). Rather than leaving the injected
`IMemoryIntegration` unused (which would have contradicted the
Objective's own literal text) or reaching into `MemoryMapper`'s private
`f"memory:{key}"` id-derivation scheme (which would have created a
hidden, fragile coupling to another package's implementation detail),
this Engineer resolved the tension by having every public method
attach `IMemoryIntegration.synchronization_status()`'s own snapshot to
its `ReasoningResult.metadata`, read-only and unconditionally - see
`argus/reasoning/engine.py`'s own Architectural Decision for the full
reasoning. This is a dependency-usage judgment call, not an
adoption-criterion question, and does not itself bear on ADR-0002 -
recorded here only because it was discovered in the course of this
same package's IService integration work.

Ten adopters now exist (Scheduler, IntentRouter, WorkflowEngine,
ConversationManager, IntentDispatcher, AgentRuntime, ConnectorManager,
KnowledgeGraph, MemoryIntegration, and now ReasoningEngine), seven of
which are genuinely gated (all but IntentRouter, KnowledgeGraph, and
ReasoningEngine). Ten core services exist that do not implement
`IService` at all (Configuration, the Logger, the Event Bus, the
Service Registry, the Lifecycle Manager, Knowledge Service, Memory
Service, Capability Registry, Plugin Manager, and Planner).

**Recommendation:** unchanged in substance. A dedicated architectural
package to resolve `IService.status()`'s duplication is still
warranted, now for ten adopters rather than nine. This package's
finding, read alongside Packages 018 and 019, further strengthens the
case that ADR-0002 could usefully be revised to formally separate
"adoption" (whether a class implements `IService` - which may be
directed or derived) from "gating" (which specific methods are gated
on `RUNNING` - which remains this Engineer's own criterion-driven
judgment call regardless of how adoption was decided), now backed by
three consecutive directed-adoption data points (two divergent, one
convergent) rather than two. This ADR's Status remains `Proposed`, per
standing instruction; only the Founder/Architect elevates it to
`Accepted`, revises its text, or opens the follow-up package.

## Empirical Finding (Package 021 - Decision Engine)

`IDecisionEngine`, per the Founder's Package 021 work order, DOES
inherit `IService` - again an explicit instruction, not this
Engineer's own judgment call. Applying ADR-0002's criterion
independently to this package's actual methods, however, would NOT
have suggested adoption on its own - the same divergence Package
018's Knowledge Graph and Package 020's Reasoning Engine both
exhibited. All six public methods (`evaluate()`, `evaluate_all()`,
`register_rule()`, `remove_rule()`, `list_rules()`,
`decision_summary()`) are synchronous, in-memory operations: the two
evaluation methods call only caller-supplied, in-process Python
predicate functions against caller-supplied `ReasoningResult`
objects, and the four registry methods operate on this engine's own
local rule table - no external call, no dispatch, no write to
another system, and no phase distinction any of them could plausibly
be gated on. "Its responsibility is limited to deterministic decision
evaluation," per this package's own Objective - architecturally much
closer to `KnowledgeGraph` (Package 018) and `ReasoningEngine`
(Package 020), both zero-gated adopters, than to `MemoryIntegration`
(Package 019), whose genuinely gated methods perform effectful,
stateful cross-system coordination that calling a local predicate
function does not. `DecisionEngine` therefore implements the full
IService lifecycle boilerplate (`initialize()`/`start()`/`stop()`/
`status()`) but gates none of its own six public methods - exactly
mirroring `KnowledgeGraph`'s (Package 018) and `ReasoningEngine`'s
(Package 020) identical shape, making `DecisionEngine` the **fourth**
IService adopter in this codebase with zero gated methods.

This package also extends the three-consecutive-directed-adoption
pattern Package 020's own finding identified: 018 diverged, 019
converged, 020 diverged, and now 021 diverges again - three divergent
cases against one convergent case across four consecutive packages
where `IService` adoption itself was an explicit instruction rather
than this Engineer's own judgment call. This further strengthens the
recommendation (first raised in Package 019's finding, restated in
Package 020's) that ADR-0002 be revised to formally separate
"adoption" (directed or derived) from "gating" (always this
Engineer's own criterion-driven judgment, regardless of the first
answer's source) - the pattern is now consistent enough across four
data points that treating them as a single combined decision, as the
ADR's current text implicitly does, increasingly understates how
independent the two questions actually are in practice.

A distinct, related design point also surfaced in this package, worth
recording separately from the adoption question itself: this
package's own Bootstrap section lists the Reasoning Engine as a
dependency ("Decision Engine depends on: Reasoning Engine"), and
`DecisionEngine`'s constructor genuinely accepts an injected
`IReasoningEngine` - but, unlike Package 020's Reasoning Engine (which
genuinely calls its own injected `IMemoryIntegration
.synchronization_status()` on every call), `DecisionEngine` never
calls any method on its injected `IReasoningEngine` in Version 1. Two
things distinguish this package's situation from Package 020's, not
merely a stylistic choice: first, this package's own Objective
describes `evaluate()`/`evaluate_all()` operating on `ReasoningResult`
objects the caller already supplies, never on a live
`IReasoningEngine` reference queried internally - unlike Package 020's
own Objective, which explicitly stated the Reasoning Engine itself
"consumes information from... Memory Integration." Second,
`IReasoningEngine` has no equivalent to
`IMemoryIntegration.synchronization_status()`'s zero-argument,
whole-system snapshot - every one of its six public methods requires
a specific, meaningful query parameter that `DecisionEngine` has no
principled, non-arbitrary way to supply blindly on every call.
Manufacturing a call (for example, to the inherited, always-`CREATED`
`status()`) purely to claim "genuine use" would have been decorative,
not functional - so the dependency is wired (constructor-injected,
per the explicit Bootstrap instruction, ready for a future package to
extend) but honestly left uncalled, a third distinct shape from this
codebase's two prior precedents (Package 018's Planner/Knowledge
Graph relationship, not wired into the constructor at all at the
time, and Package 020's Reasoning Engine/Memory Integration
relationship, wired and genuinely called every time). This is a
dependency-usage judgment call, not an adoption-criterion question,
and does not itself bear on ADR-0002 - recorded here only because it
was discovered in the course of this same package's IService
integration work, and because it is the direct architectural
counterpart to Package 020's own equivalent finding about its
Memory Integration dependency.

Eleven adopters now exist (Scheduler, IntentRouter, WorkflowEngine,
ConversationManager, IntentDispatcher, AgentRuntime, ConnectorManager,
KnowledgeGraph, MemoryIntegration, ReasoningEngine, and now
DecisionEngine), seven of which are genuinely gated (all but
IntentRouter, KnowledgeGraph, ReasoningEngine, and DecisionEngine).
Ten core services exist that do not implement `IService` at all
(Configuration, the Logger, the Event Bus, the Service Registry, the
Lifecycle Manager, Knowledge Service, Memory Service, Capability
Registry, Plugin Manager, and Planner).

**Recommendation:** unchanged in substance. A dedicated architectural
package to resolve `IService.status()`'s duplication is still
warranted, now for eleven adopters rather than ten. This package's
finding, read alongside Packages 018-020, makes an even stronger case
that ADR-0002 could usefully be revised to formally separate
"adoption" from "gating" as distinct questions, now backed by four
consecutive directed-adoption data points (three divergent, one
convergent) rather than three. This ADR's Status remains `Proposed`,
per standing instruction; only the Founder/Architect elevates it to
`Accepted`, revises its text, or opens the follow-up package.

---

## Empirical Finding (Package 025 - Cognitive Pipeline)

`ICognitivePipeline`, per the Founder's Package 025 work order, DOES
inherit `IService` - once again an explicit instruction, not this
Engineer's own judgment call ("Register the Cognitive Pipeline as a
core service. This is the first new runtime service since Package
021."). Applying ADR-0002's criterion independently to this package's
one public method, however, WOULD have suggested adoption on its own
this time - the same convergence Package 019's Memory Integration
exhibited, and the direct opposite of Packages 018, 020, and 021's
divergent pattern. `CognitivePipeline` has exactly one public method,
`run()`, and it is not a synchronous, in-memory, single-system lookup
of the kind `KnowledgeGraph.query()` (Package 018),
`ReasoningEngine.infer()` (Package 020), or
`DecisionEngine.evaluate()` (Package 021) perform. `run()` builds two
fresh, immutable transport objects in sequence - a `CognitiveContext`
via `ContextBuilder`, then a `PlanningSession` via
`PlanningSessionBuilder`, the second embedding the first - and then
invokes a live, injected `Planner` service's own `plan_session()`,
propagating the resulting `Plan` (and any exception it raises)
straight back to the caller. This is genuinely effectful, multi-step
orchestration across a live downstream service, architecturally the
same kind of "active work" that made `ConversationManager.receive()`
(Package 011), `AgentRuntime`'s pause/cancel/get/list surface (Package
016), `ConnectorManager.invoke()` (Package 017), and
`MemoryIntegration`'s three methods (Package 019) genuinely gated,
rather than the zero-gated shape of Packages 009, 018, 020, and 021.
`CognitivePipeline` therefore gates its sole public method
(`run()` raises `PipelineError` unless `status()` is `RUNNING`) -
making it the **second** IService adopter in this codebase, after
Memory Integration (Package 019), where explicit instruction-to-adopt
and ADR-0002's criterion applied independently arrive at the same
answer, rather than diverging as in Packages 018, 020, and 021.

This finding also updates the running tally the last four packages'
findings have been building. Packages 018, 020, and 021 diverged
(instructed to adopt; criterion alone would not have gated anything);
Package 019 converged; and now Package 025 converges a second time.
Read across all five directed-adoption data points to date, the
picture is three divergent, two convergent - not yet enough to call
either shape "typical," but enough to reinforce, for a second time,
that "was `IService` adoption itself instructed" and "does the
criterion's own gating logic agree" remain genuinely independent
questions, exactly as Package 019's finding first proposed and
Packages 020-021's findings each restated.

A related, narrower point specific to this package: `CognitivePipeline`
is the first `IService` adopter in this codebase to hold no
`IEventBus` reference at all. Every other adopter, gated or not,
either publishes events directly or is positioned to in a future
version; `CognitivePipeline` was explicitly instructed not to ("Pipeline
shall not: perform direct event publication. No new EventTypes. Reuse
existing planner behavior."), and Version 1 gives it no work that
would require one - all events the pipeline's own orchestration causes
(`PLAN_CREATED`, `PLAN_UPDATED`) fire from inside `Planner
.plan_session()`'s own already-existing delegated calls, not from the
pipeline itself. This is a dependency-shape observation, not an
adoption-criterion question, and does not itself bear on ADR-0002 -
recorded here only because it was discovered in the course of this
same package's IService integration work, and because it is the
clearest example yet in this codebase of an adopter whose gating is
justified purely by orchestration effect, not by any event it emits.

Twelve adopters now exist (Scheduler, IntentRouter, WorkflowEngine,
ConversationManager, IntentDispatcher, AgentRuntime, ConnectorManager,
KnowledgeGraph, MemoryIntegration, ReasoningEngine, DecisionEngine,
and now CognitivePipeline), eight of which are genuinely gated (all
but IntentRouter, KnowledgeGraph, ReasoningEngine, and DecisionEngine).
Ten core services exist that do not implement `IService` at all
(Configuration, the Logger, the Event Bus, the Service Registry, the
Lifecycle Manager, Knowledge Service, Memory Service, Capability
Registry, Plugin Manager, and Planner).

**Recommendation:** unchanged in substance. A dedicated architectural
package to resolve `IService.status()`'s duplication is still
warranted, now for twelve adopters rather than eleven. This package's
finding, read alongside Packages 018-021, keeps the case for formally
separating "adoption" from "gating" as distinct questions open rather
than settled - now five directed-adoption data points (three
divergent, two convergent) instead of four (three divergent, one
convergent). This ADR's Status remains `Proposed`, per standing
instruction; only the Founder/Architect elevates it to `Accepted`,
revises its text, or opens the follow-up package.

---

## Empirical Finding (Package 026 - Agent Session)

`IAgentService`, per the Founder's Package 026 work order, DOES
inherit `IService` - once again an explicit instruction ("Register
AgentService as the next core service"), read the same way
`ICognitivePipeline`'s own "Register the Cognitive Pipeline as a core
service" instruction was read in Package 025 - "core service" is this
codebase's own established shorthand for "adopts IService," further
confirmed here by this package's own Testing section naming "lifecycle
behavior" as an explicit test category. Applying ADR-0002's criterion
independently to `AgentService`'s one public method, `run()`, would
have suggested adoption on its own too - the same convergence Package
019's Memory Integration and Package 025's Cognitive Pipeline each
exhibited, and the direct opposite of Packages 018, 020, and 021's
divergent pattern. `run()` validates an `AgentRequest`, builds a
`PipelineRequest` from it, and invokes a live, injected
`ICognitivePipeline`'s own `run()` - genuinely effectful, single-step
delegation to a live downstream service, architecturally the same
shape that made `CognitivePipeline.run()` itself (Package 025)
genuinely gated one layer below. `AgentService` therefore gates its
sole public method (`run()` raises `AgentError` unless `status()` is
`RUNNING`) - making it the **third** IService adopter in this
codebase, after Memory Integration (Package 019) and the Cognitive
Pipeline (Package 025), where explicit instruction-to-adopt and
ADR-0002's criterion applied independently arrive at the same answer,
rather than diverging as in Packages 018, 020, and 021.

This finding also extends the running tally three consecutive
convergent findings now hold at the top of this ADR's own history:
Packages 018, 020, and 021 diverged; Packages 019, 025, and now 026
converged. Read across all six directed-adoption data points to date,
the picture is now an even three divergent, three convergent - the
first point in this ADR's own history where the two shapes are
exactly balanced, rather than one outnumbering the other. This does
not settle which shape is "typical" any more than five points did,
but the balance itself is worth recording: it weakens, for the first
time, any reading of the earlier data as a mere run of divergent
cases followed by rare convergent exceptions, and strengthens the
recommendation - unchanged in substance since Package 019's own
finding - that "was IService adoption instructed" and "does the
criterion's own gating logic agree" are best treated as genuinely
independent questions in any future revision of this ADR's text.

A related, narrower point specific to this package, directly
mirroring Package 025's own equivalent observation one layer below:
`AgentService` is the second `IService` adopter in this codebase
(after `CognitivePipeline`, Package 025) to hold no `IEventBus`
reference at all. "No event publication" is explicit in this
package's own AgentService Responsibilities, and Version 1 gives it no
work that would require one - the one event any given `run()` call
might eventually cause (`PLAN_CREATED`, `PLAN_UPDATED`) still fires
from inside `Planner.plan_session()`'s own pre-existing delegated
calls, two layers below `AgentService` itself. This is a
dependency-shape observation, not an adoption-criterion question, and
does not itself bear on ADR-0002 - recorded here only because it was
discovered in the course of this same package's IService integration
work, and because it is now the second consecutive new-service package
to exhibit this exact shape, suggesting "orchestration-only, no
IEventBus" may be becoming this codebase's own default pattern for any
future package whose entire contribution is delegating to an
already-instrumented downstream service.

Thirteen adopters now exist (Scheduler, IntentRouter, WorkflowEngine,
ConversationManager, IntentDispatcher, AgentRuntime, ConnectorManager,
KnowledgeGraph, MemoryIntegration, ReasoningEngine, DecisionEngine,
CognitivePipeline, and now AgentService), nine of which are genuinely
gated (all but IntentRouter, KnowledgeGraph, ReasoningEngine, and
DecisionEngine). Ten core services exist that do not implement
`IService` at all (Configuration, the Logger, the Event Bus, the
Service Registry, the Lifecycle Manager, Knowledge Service, Memory
Service, Capability Registry, Plugin Manager, and Planner).

**Recommendation:** unchanged in substance. A dedicated architectural
package to resolve `IService.status()`'s duplication is still
warranted, now for thirteen adopters rather than twelve. This
package's finding, read alongside Packages 018-021 and 025, makes the
strongest case yet - now six directed-adoption data points, evenly
split three divergent and three convergent - that ADR-0002 could
usefully be revised to formally separate "adoption" from "gating" as
distinct questions. This ADR's Status remains `Proposed`, per standing
instruction; only the Founder/Architect elevates it to `Accepted`,
revises its text, or opens the follow-up package.

---

## Empirical Finding (Package 027 - Response Engine)

`IResponseEngine`, per the Founder's Package 027 work order, DOES
inherit `IService` - once again read the same way `ICognitivePipeline`'s
(Package 025) and `IAgentService`'s (Package 026) own "Register ... as
a core service" instructions were read: this package's own Bootstrap
section says only "Register: ResponseEngine," less explicit than
either of those two, but its own Testing section names "lifecycle" as
an explicit verification category, the same tell that confirmed the
reading for Package 026. Applying ADR-0002's criterion to
`build_response()` independently, however, would NOT have suggested
adoption on its own - the same divergence Packages 018, 020, and 021
each exhibited, and the direct opposite of Packages 019, 025, and
026's convergent pattern. `build_response()` is a synchronous,
in-memory transformation of a `Plan` the caller already supplies - no
external call, no dispatch to another live service, and no phase
distinction it could plausibly be gated on, since "ResponseEngine may
depend only on: Plan" leaves it with no live collaborator to gate
access to in the first place. This is architecturally the same shape
as `KnowledgeGraph` (Package 018), `ReasoningEngine` (Package 020),
and `DecisionEngine` (Package 021) - each explicitly instructed to
adopt IService, each with no method gated on the RUNNING state - and
takes that shape one step further: unlike those three, which each
hold at least one constructor-injected collaborator (an `IEventBus`,
in every case) even though their own domain methods never call into
it for gating purposes, `ResponseEngine.__init__()` takes no
constructor dependency at all - the first core service in this
codebase for which that is true. `ResponseEngine` therefore implements
the full IService lifecycle boilerplate
(`initialize()`/`start()`/`stop()`/`status()`) but gates nothing -
making it the **fifth** IService adopter in this codebase with zero
gated methods (after IntentRouter, KnowledgeGraph, ReasoningEngine,
and DecisionEngine), and the **fourth** case where an explicit
instruction to adopt IService diverges from what ADR-0002's own
criterion would independently conclude (after Packages 018, 020, and
021).

This finding also breaks the exact three-divergent/three-convergent
tie Package 026's own finding established - the first point in this
ADR's own history where the two shapes were perfectly balanced,
across six directed-adoption data points. Package 027 tips the
balance back toward divergent: four divergent (018, 020, 021, 027)
against three convergent (019, 025, 026) across seven data points.
Read as a single sequence, the pattern so far is 018-divergent,
019-convergent, 020-divergent, 021-divergent, 025-convergent,
026-convergent, 027-divergent - no run longer than two in either
direction, and no obvious alternation either. This continues to
resist any confident claim about which shape is "typical" for a
directed IService adoption in this codebase, which is itself the
core of the recommendation every finding since Package 019 has
repeated: "was adoption instructed" and "does the criterion agree"
are better modeled as two independent questions than as one combined
decision.

A related, narrower point specific to this package: `ResponseEngine`
is the first core service in this codebase's own history - adopter or
not - with a fully empty constructor. Every other core service,
including every zero-gated `IService` adopter before it
(`IntentRouter`, `KnowledgeGraph`, `ReasoningEngine`, `DecisionEngine`),
takes at least one constructor dependency, typically an `IEventBus`,
even when that dependency is never used for gating. `ResponseEngine`
has no dependency of any kind - not because its own methods happen
not to need one for gating, but because its own Dependency Rules
("ResponseEngine may depend only on: Plan") make `Plan` a per-call
argument rather than a constructor-injected collaborator, the first
time in this codebase a core service's *sole* permitted dependency is
something that arrives with every call rather than something wired in
once at construction. This is a dependency-shape observation, not an
adoption-criterion question, and does not itself bear on ADR-0002 -
recorded here only because it was discovered in the course of this
same package's IService integration work, and because it is a genuine
first for this codebase's own core-service population.

Fourteen adopters now exist (Scheduler, IntentRouter, WorkflowEngine,
ConversationManager, IntentDispatcher, AgentRuntime, ConnectorManager,
KnowledgeGraph, MemoryIntegration, ReasoningEngine, DecisionEngine,
CognitivePipeline, AgentService, and now ResponseEngine), nine of
which are genuinely gated (all but IntentRouter, KnowledgeGraph,
ReasoningEngine, DecisionEngine, and now ResponseEngine). Ten core
services exist that do not implement `IService` at all (Configuration,
the Logger, the Event Bus, the Service Registry, the Lifecycle
Manager, Knowledge Service, Memory Service, Capability Registry,
Plugin Manager, and Planner).

**Recommendation:** unchanged in substance. A dedicated architectural
package to resolve `IService.status()`'s duplication is still
warranted, now for fourteen adopters rather than thirteen. This
package's finding, breaking the first-ever divergent/convergent tie
this ADR's own history produced, makes the strongest case yet - seven
directed-adoption data points, four divergent and three convergent,
no discernible pattern to when each shape occurs - that ADR-0002
could usefully be revised to formally separate "adoption" from
"gating" as distinct questions, rather than continuing to treat each
new package's own combination as a fresh, independent surprise. This
ADR's Status remains `Proposed`, per standing instruction; only the
Founder/Architect elevates it to `Accepted`, revises its text, or
opens the follow-up package.

---

## Empirical Finding (Package 032 - Execution Engine)

`IExecutionEngine`, per the Founder's Package 032 work order, DOES
inherit `IService` - read the same way "Register: ResponseEngine"
(027) was: this package's own Bootstrap section says only "Register:
ExecutionEngine. One new core service," with no further elaboration,
but "core service" remains this codebase's own established shorthand
for "adopts IService" (see argus/response/interfaces.py's own
identical Architectural Note, and every prior directed-adoption
finding in this file). Applying ADR-0002's criterion to `execute()`
independently, however, would NOT have suggested adoption on its own
- the identical divergence Packages 018, 020, 021, and 027 each
exhibited. `execute()` is a synchronous, in-memory transformation of a
`Plan` the caller already supplies - no external call, no dispatch to
another live service, and no phase distinction it could plausibly be
gated on, since `ExecutionEngine`'s own constructor takes no
dependency at all (see engine.py's own module docstring). This is
architecturally the identical shape to `ResponseEngine` (027) - "no
live collaborator to gate access to in the first place" - making
`IExecutionEngine` the **sixth** IService adopter in this codebase
with zero gated methods (after IntentRouter, KnowledgeGraph,
ReasoningEngine, DecisionEngine, and ResponseEngine), and the
**fifth** case where an explicit instruction to adopt IService
diverges from what ADR-0002's own criterion would independently
conclude (after Packages 018, 020, 021, and 027).

This finding extends the divergent/convergent split Package 027's own
finding tipped away from parity: five divergent (018, 020, 021, 027,
032) against three convergent (019, 025, 026) across eight directed-
adoption data points. Read as a single sequence, the pattern so far is
018-divergent, 019-convergent, 020-divergent, 021-divergent,
025-convergent, 026-convergent, 027-divergent, 032-divergent - the
first run of two consecutive divergent findings this ADR's own history
has produced. This is still not enough evidence to claim divergence is
"typical" outright, but it is the first data point that mildly
favors that reading over the near-parity every prior finding had
maintained.

A related, narrower point specific to this package, extending
Package 027's own "first empty constructor" observation:
`ExecutionEngine` is only the **second** core service in this
codebase's own history - after `ResponseEngine` (027) - with a fully
empty constructor. Its own sole "dependency," the `Plan` it processes,
is a per-call argument to `execute()`, never a constructor-injected
collaborator, for the identical reason `ResponseEngine`'s own `Plan`
dependency is per-call rather than constructor-injected. This remains
a dependency-shape observation, not an adoption-criterion question,
recorded here only because it was discovered in the course of this
same package's IService integration work.

Fifteen adopters now exist (Scheduler, IntentRouter, WorkflowEngine,
ConversationManager, IntentDispatcher, AgentRuntime, ConnectorManager,
KnowledgeGraph, MemoryIntegration, ReasoningEngine, DecisionEngine,
CognitivePipeline, AgentService, ResponseEngine, and now
ExecutionEngine), nine of which are genuinely gated (all but
IntentRouter, KnowledgeGraph, ReasoningEngine, DecisionEngine,
ResponseEngine, and now ExecutionEngine). Ten core services exist that
do not implement `IService` at all (Configuration, the Logger, the
Event Bus, the Service Registry, the Lifecycle Manager, Knowledge
Service, Memory Service, Capability Registry, Plugin Manager, and
Planner) - unchanged by this package.

**Recommendation:** unchanged in substance. A dedicated architectural
package to resolve `IService.status()`'s duplication is still
warranted, now for fifteen adopters rather than fourteen. This
package's finding, producing this ADR's own first run of two
consecutive divergent findings, makes the case for formally separating
"adoption" from "gating" as distinct questions somewhat stronger still
- eight directed-adoption data points, five divergent and three
convergent, with divergence now trending rather than merely tied. This
ADR's Status remains `Proposed`, per standing instruction; only the
Founder/Architect elevates it to `Accepted`, revises its text, or
opens the follow-up package.

## Empirical Finding (Package 034 - Capability Executor)

`ICapabilityExecutor`, per the Founder's Package 034 work order, DOES
inherit `IService` - read the same way "Register: ExecutionEngine.
One new core service" (032) and "Register: ResponseEngine" (027)
were: this package's own Bootstrap section says only "Register:
CapabilityExecutor as a core service," with no further elaboration,
but "core service" remains this codebase's own established shorthand
for "adopts IService." Applying ADR-0002's criterion to `resolve()`
independently, however, would NOT have suggested adoption on its own -
the identical divergence Packages 018, 020, 021, 027, and 032 each
exhibited. `resolve()` is a synchronous, read-only, in-memory lookup
against an already-injected `ICapabilityRegistry` - one deterministic
"does a Capability with this name exist" question, no external call,
no dispatch to another live service beyond that single collaborator,
no write, and no phase distinction it could plausibly be gated on.
This makes `ICapabilityExecutor` the **seventh** IService adopter in
this codebase with zero gated methods (after IntentRouter,
KnowledgeGraph, ReasoningEngine, DecisionEngine, ResponseEngine, and
ExecutionEngine), and the **sixth** case where an explicit instruction
to adopt IService diverges from what ADR-0002's own criterion would
independently conclude (after Packages 018, 020, 021, 027, and 032).

A narrower point distinguishes this finding from the two immediately
preceding it: unlike `ResponseEngine` (027) and `ExecutionEngine`
(032), whose own zero-gated status rests on holding no constructor
dependency whatsoever, `CapabilityExecutor` holds a genuine
constructor dependency (`ICapabilityRegistry`) that `resolve()`
genuinely calls on every invocation - architecturally the identical
shape to `KnowledgeGraph` (018), `ReasoningEngine` (020), and
`DecisionEngine` (021), each also zero-gated despite holding a real,
called constructor dependency, since none of their own methods
perform an effectful, stateful, or external operation a
RUNNING/not-RUNNING distinction could meaningfully police. This
finding therefore extends the "genuine dependency, still zero-gated"
sub-pattern first identified at Package 018, not the "no dependency at
all" sub-pattern Packages 027 and 032 each established.

This finding also extends the divergent/convergent split Package 032's
own finding tipped into its first run of two consecutive divergent
findings: six divergent (018, 020, 021, 027, 032, 034) against three
convergent (019, 025, 026) across nine directed-adoption data points
(Package 033 contributed no new directed-adoption data point at all -
`ICapabilityBuilder` does not inherit `IService`, and no other new
adopter was introduced that package). Read as a single sequence, the
pattern so far is 018-divergent, 019-convergent, 020-divergent,
021-divergent, 025-convergent, 026-convergent, 027-divergent,
032-divergent, 034-divergent - the first run of *three* consecutive
divergent findings this ADR's own history has produced, extending
Package 032's own first run of two. This further strengthens, without
yet confirming outright, the reading that divergence - rather than
convergence - is the more typical shape for this codebase's own
explicitly-directed IService adoptions.

Sixteen adopters now exist (Scheduler, IntentRouter, WorkflowEngine,
ConversationManager, IntentDispatcher, AgentRuntime, ConnectorManager,
KnowledgeGraph, MemoryIntegration, ReasoningEngine, DecisionEngine,
CognitivePipeline, AgentService, ResponseEngine, ExecutionEngine, and
now CapabilityExecutor), nine of which are genuinely gated (all but
IntentRouter, KnowledgeGraph, ReasoningEngine, DecisionEngine,
ResponseEngine, ExecutionEngine, and now CapabilityExecutor). Ten core
services exist that do not implement `IService` at all (Configuration,
the Logger, the Event Bus, the Service Registry, the Lifecycle
Manager, Knowledge Service, Memory Service, Capability Registry,
Plugin Manager, and Planner) - unchanged by this package, since
`CapabilityExecutor` is a new core service distinct from the
pre-existing Capability Registry.

**Recommendation:** unchanged in substance. A dedicated architectural
package to resolve `IService.status()`'s duplication is still
warranted, now for sixteen adopters rather than fifteen. This
package's finding, producing this ADR's own first run of three
consecutive divergent findings, makes the case for formally separating
"adoption" from "gating" as distinct questions somewhat stronger
still - nine directed-adoption data points, six divergent and three
convergent, with divergence now the clear majority shape rather than a
narrow lean. This ADR's Status remains `Proposed`, per standing
instruction; only the Founder/Architect elevates it to `Accepted`,
revises its text, or opens the follow-up package.
