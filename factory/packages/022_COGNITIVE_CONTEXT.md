# Implementation Package 022 - Cognitive Context

## Objective

Give ArgusOS a first-generation Cognitive Context: an immutable
transport object that carries one reasoning cycle's accumulated
state - a conversation identifier, memory/knowledge/decision
reference identifiers, reasoning results, and descriptive metadata -
through the cognitive pipeline. "It represents the complete state of
a reasoning cycle... It does not perform reasoning. It does not make
decisions. It does not execute plans. It is a transport object
only." Per the Founder's Package 022 work order, neither the Planner
nor the Decision Engine consume it yet - "Package 022 introduces the
abstraction only" - and, unlike every prior infrastructure package in
this codebase, it registers no new core service, publishes no new
events, and leaves `argus/bootstrap.py` completely untouched.

```
Conversation -> Memory Service -> Memory Integration -> Knowledge Graph -> Reasoning Engine -> Cognitive Context -> Decision Engine -> Planner -> Validated Plan -> Agent Runtime
```

The Cognitive Context is the only component responsible for carrying
a reasoning cycle's accumulated references and results forward as a
single, immutable unit. It stores nothing beyond the fields it is
given; it never mutates memory, the Knowledge Graph, a Decision, or
anything else, never invokes a Planner, Reasoning Engine, Decision
Engine, or any other service, and owns no persistence of its own.

---

## Specification Note

No `design/specifications/COGNITIVE_CONTEXT.md` exists in the
repository - the same situation as Packages 002, 009-021. This
package is built directly from the Founder's explicit work order.

---

## Context Model

`CognitiveContext` (`argus/context/context.py`) is an immutable value
object:

```
context_id: str = <uuid4>
conversation_id: Optional[str] = None
memory_references: Sequence[str] = ()
knowledge_references: Sequence[str] = ()
reasoning_results: Sequence[ReasoningResult] = ()
decision_references: Sequence[str] = ()
metadata: ContextMetadata = <fresh ContextMetadata>
```

`reasoning_results` holds the actual, already-immutable
`ReasoningResult` objects (Package 020) - directly reusing
`Decision.reasoning_results`' (Package 021) own field name and type.
`memory_references`, `knowledge_references`, and
`decision_references` hold plain identifier strings, not live
objects - `MemoryRecord` keys, Knowledge Graph Entity/Relationship
ids, and `Decision.decision_id` values, respectively (see
Architectural Decision 1). Every field is immutable; sequences are
wrapped in `tuple`, matching every other value object in this
codebase. Like every other value object in this codebase,
`CognitiveContext` performs no validation of its own - see
Architectural Decision 2.

---

## Metadata Model

`ContextMetadata` (`argus/context/metadata.py`) is an immutable value
object:

```
created_at: datetime = <now, UTC>
version: str = "1.0"
correlation_id: str = <uuid4>
extra: Mapping[str, Any] = {}
```

Reconciles the work order's two descriptions of "metadata" - the
Responsibilities section's "arbitrary metadata" and the dedicated
Metadata section's "creation timestamp, version, correlation
identifier" - into a single field: `created_at`/`version`/
`correlation_id` are the named, system-assigned fields, and `extra`
is the open-ended mapping a caller populates via
`ContextBuilder.with_metadata()` (see Architectural Decision 3).
`version` here is the Cognitive Context schema version, unrelated to
`CORE_SERVICES_VERSION` (`argus/bootstrap.py`).

---

## Builder Architecture

`ContextBuilder` (`argus/context/builder.py`) implements
`ICognitiveContextBuilder`:

```
with_conversation(conversation_id)  -> ContextBuilder
with_memory(reference_id)           -> ContextBuilder
with_knowledge(reference_id)        -> ContextBuilder
with_reasoning(reasoning_result)    -> ContextBuilder
with_decision(reference_id)         -> ContextBuilder
with_metadata(key, value)           -> ContextBuilder
build()                             -> CognitiveContext
```

- "The builder is mutable. The resulting context is immutable."
  Every `with_*` method validates its own argument, mutates this
  builder's private accumulator state, and returns `self`, so calls
  chain fluently.
- `with_memory()`, `with_knowledge()`, `with_reasoning()`, and
  `with_decision()` each accumulate across multiple calls (list
  fields); `with_conversation()` overwrites on each call (a single
  scalar field) - last call before `build()` wins. `with_metadata()`
  accumulates distinct keys and overwrites on a repeated key, the
  same last-call-wins rule (see Architectural Decision 4).
- `build()` performs no additional validation - every accumulated
  value was already validated at the point it was added - and
  constructs a fresh, independent `CognitiveContext` (with a fresh
  `ContextMetadata`) from the builder's current state every time it
  is called (see Architectural Decision 5).

---

## Builder Lifecycle

```
        caller constructs ContextBuilder()
                    |
                    v
    zero or more with_*(...) calls, each:
           |                        |
      invalid input              valid input
           |                        |
           v                        v
  InvalidContextError        accumulate into
    (raised immediately,      builder's private
     builder state              state; return self
     unchanged)                 for chaining
                                     |
                                     v
                                caller calls build()
                                     |
                                     v
                     construct + return a fresh,
                     independent CognitiveContext
                     (fresh ContextMetadata) from
                     the builder's current state
```

`build()` may be called any number of times on the same builder,
including after further `with_*()` calls - each call returns its own
independent `CognitiveContext` snapshot; earlier snapshots are never
retroactively affected. No event is published at any point in this
lifecycle - "This package is intentionally passive."

---

## Dependency Graph

```
CognitiveContext
    depends on -> ReasoningResult   (Package 020; typing only, for the
                                      reasoning_results field)
    depends on -> ContextMetadata   (this package)

ContextBuilder
    depends on -> CognitiveContext  (this package)
    depends on -> ReasoningResult   (Package 020; with_reasoning()'s
                                      own type check)

Decision Engine, Reasoning Engine, Planner, Agent Runtime
    do NOT depend on CognitiveContext or ContextBuilder in Version 1 -
    "Planner shall not consume it yet. Decision Engine shall not
    consume it yet."
```

No construction order entry exists in `bootstrap.py` for this
package - `CognitiveContext`/`ContextBuilder` are plain value objects
any caller constructs directly, exactly like `Entity` or
`ReasoningQuery`, not a registered core service (see Architectural
Decision 6).

---

## Architectural Decisions

### 1. Three fields hold bare identifier strings; one holds live objects

`memory_references`, `knowledge_references`, and
`decision_references` hold plain identifier strings rather than the
live `MemoryRecord`/`Entity`/`Relationship`/`Decision` objects
themselves - matching the work order's own naming distinction
("...references" vs. "reasoning_results"). This is what makes "shall
NOT modify any contained object" and "shall NOT own persistence" true
by construction: a `CognitiveContext` holding only strings for these
three fields has no live object graph to accidentally mutate or be
responsible for persisting, and introduces no coupling to
`argus.memory_integration`'s or `argus.knowledge_graph`'s own concrete
value-object shapes. `reasoning_results`, by contrast, holds the
actual `ReasoningResult` objects, directly reusing
`Decision.reasoning_results`' (Package 021) own field name and type.

### 2. `CognitiveContext` performs no validation of its own

Like `Entity`, `Relationship`, `ReasoningQuery`, `ReasoningResult`,
`DecisionRule`, and `Decision` before it, `CognitiveContext` is a
pure value object - all validation lives in `ContextBuilder`, this
package's equivalent of a "consuming service" for validation
purposes, even though `ContextBuilder` is not an `IService` and a
`CognitiveContext` is never "stored" anywhere. `CognitiveContext`
remains directly constructible without going through `ContextBuilder`
at all, for the same reason every other value object in this codebase
is: a pure data holder should not force callers through one
particular construction path.

### 3. `ContextMetadata` combines named fields and an open `extra` mapping

The work order describes "metadata" two different ways - the
Responsibilities section's "arbitrary metadata" and the dedicated
Metadata section's specific named fields. Rather than adding two
separate metadata-shaped fields to `CognitiveContext`, `ContextMetadata`
holds both: `created_at`/`version`/`correlation_id` as named,
system-assigned fields, plus one `extra: Mapping[str, Any]` field for
genuinely open-ended, caller-supplied data. `ContextBuilder.with_metadata()`
only ever populates `extra` - the three named fields are never
caller-settable through the builder's fluent interface.

### 4. `with_conversation()`/`with_metadata()` overwrite; the other four `with_*` methods accumulate

`conversation_id` is a single scalar field, so calling
`with_conversation()` more than once simply replaces the previous
value - the same "last call wins" rule applied to repeated
`with_metadata()` calls using the same key. `with_memory()`,
`with_knowledge()`, `with_reasoning()`, and `with_decision()` each
append to a `Sequence`-typed field, so repeated calls accumulate -
this is what makes "fluent construction" (calling a `with_*` method
several times to build up a collection) meaningful for those four
methods.

### 5. `build()` always returns an independent snapshot

`CognitiveContext.__post_init__` copies every mutable
sequence/mapping it is given into a `tuple`/`MappingProxyType`, so a
`CognitiveContext` returned by one `build()` call is never
retroactively affected by further `with_*()` calls on the same
builder, or by a second `build()` call - each `build()` also
constructs a brand-new `ContextMetadata` (with its own fresh
`created_at`/`correlation_id`), so no two `build()` calls, even with
identical builder state, produce metadata-identical contexts unless
the caller explicitly supplies identical values.

### 6. No new core service, no bootstrap changes, no `IService`

Per this package's own explicit instruction: "This is not an
IService... This package intentionally introduces no new core
service. This is the first infrastructure package since the early
foundation that does not expand the service registry." Unlike
`IConnectorManager`, `IKnowledgeGraph`, `IReasoningEngine`, and
`IDecisionEngine` (all of which inherit `IService`, whether or not
any of their methods end up gated), `ICognitiveContextBuilder`
extends plain `ABC` - matching `IConnector`'s (Package 017) own
precedent for "a contract that is plain behavior, not a
lifecycle-managed service." `argus/bootstrap.py` was not modified in
any way by this package.

---

## Events

None. "No new EventTypes. This package is intentionally passive." No
`with_*` method or `build()` publishes anything - every operation
either mutates this builder's own private, in-process accumulator
state or constructs a plain value object, neither of which is the
kind of externally-visible occurrence this codebase's `EventType`
convention exists to announce.

---

## IService Adoption

Not applicable. `ICognitiveContextBuilder` does not inherit
`IService` - this package is the first infrastructure package since
the early foundation not to register a new core service, per
explicit instruction. `design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md`
was not modified by this package - it records only `IService`
adopters, and this package introduces none.

---

## Repository Verification Note

The uploaded repository ("ArgusOS (21).zip") was verified against
this package's own general "verify repository state, verify version
consistency, verify HEAD/tag ancestry, run smoke validation"
pre-flight instruction. Findings: HEAD (`28b9502`, "Synchronize
repository version with v0.2.1 release") is a clean, single-commit
descendant of tag `v0.2.1` (which points to `e6d578a`, "Implement
Package 021 Decision Engine"); `v0.2.0` also confirmed an ancestor of
HEAD via `git merge-base --is-ancestor`. `git diff v0.2.1..HEAD --stat`
shows exactly the expected one-line version-sync commit
(`argus/bootstrap.py`, 1 insertion, 1 deletion) - no anomaly.
`git status --short` showed a completely clean working tree.
`argus/decision/` (Package 021) present with all expected files;
`python -m pytest` passing (1269 passed, 38 subtests); `python -m
unittest discover -s tests` passing (1181); `python -m unittest
discover -s argus/tests` passing (64); `python main.py` starting and
shutting down cleanly (exit 0); `CORE_SERVICES_VERSION == "0.2.1"`
matching tag `v0.2.1`. All confirmed before any Package 022 code was
written.

---

## Files Created

```
argus/
    context/
        __init__.py
        context.py
        metadata.py
        builder.py
        interfaces.py
        exceptions.py
tests/
    test_context.py
    test_context_builder.py
    test_context_metadata.py
```

## Files Modified

```
CHANGELOG.md, DEVLOG.md, IMPLEMENTATION_REPORT.md, factory/ROADMAP.md
```

No other file was modified. Per this package's own explicit
Constraints, `argus/bootstrap.py`, `argus/events/event_types.py`,
`tests/test_bootstrap.py`, `argus/tests/test_bootstrap.py`,
`argus/planner/`, `argus/decision/`, and `argus/reasoning/` were left
completely untouched - confirmed via `git diff --stat` showing zero
lines changed in any of them.

---

## Test Totals

1,237 tests passing via `python -m unittest discover -s tests` (1,181
from Packages 002-021, plus 15 new in `test_context.py`, 20 new in
`test_context_builder.py`, and 10 new in `test_context_metadata.py`).
`python -m unittest discover -s argus/tests` remains unchanged at 64
- this package touches no file inside the duplicate `argus/tests/`
tree, so no `CORE_SERVICE_NAMES` sync was needed or performed.
`python -m pytest` also passes: 1,325 passed, 38 subtests passed.

---

## Coverage

100% line coverage on every new module measured for this package:
`argus/context/__init__.py`, `argus/context/context.py`,
`argus/context/metadata.py`, `argus/context/builder.py`,
`argus/context/interfaces.py`, and `argus/context/exceptions.py` -
all 100%, no accepted gaps, reached on the first measurement.
`argus/bootstrap.py` and `argus/events/event_types.py` are not part
of this package's coverage scope, since neither was modified. Overall
repository coverage: 99% (unchanged from Package 021; remaining gaps
are pre-existing and out of scope).

---

## Known Limitations

- **No lifecycle, no service registration** - `CognitiveContext`/
  `ContextBuilder` are plain value objects with no `IService`
  contract; nothing here is started, stopped, or has a status. See
  Architectural Decision 6.
- **No events** - this package publishes nothing; see the Events
  section above.
- **No persistence, no serialization** - a `CognitiveContext` exists
  only in memory for as long as a caller holds a reference to it.
- **The Planner does not yet consume the Cognitive Context** - per
  this package's own explicit "Planner shall not consume it yet"
  Constraint.
- **The Decision Engine does not yet consume the Cognitive Context** -
  per this package's own explicit "Decision Engine shall not consume
  it yet" Constraint.
- **`memory_references`/`knowledge_references`/`decision_references`
  are opaque identifier strings** - `CognitiveContext` performs no
  lookup, dereferencing, or validation that a given identifier
  actually corresponds to an existing record; resolving one requires
  calling the relevant service (Memory Integration, Knowledge Graph,
  Decision Engine) directly, with that identifier.
- No concurrency.
- The repository's stray `argus/` duplicate tree and legacy
  pre-Factory files remain unresolved, out of scope per the Founder's
  explicit repository rules.

---

## Future Expansion

- Wire the Reasoning Engine (or a future orchestrating component) to
  construct a `CognitiveContext` via `ContextBuilder` at the end of a
  reasoning cycle, once a future package's work order explicitly asks
  for that integration.
- Wire the Decision Engine and/or Planner to accept and consume a
  `CognitiveContext`, once a concrete requirement to do so exists -
  the diagram already places `CognitiveContext` directly upstream of
  both.
- Consider whether a future package should add identifier-resolution
  helpers (for example, dereferencing `memory_references` back into
  `MemoryRecord` objects via Memory Integration) once a concrete
  consumer needs it - Version 1 deliberately keeps `CognitiveContext`
  free of any such live-service dependency.

---

## Release Rules

Per the Founder's explicit instruction: no commit, tag, or push was
performed. `CORE_SERVICES_VERSION` was not changed by this package -
it remains `"0.2.1"`. This package is not reported as complete or
released - implementation ends after successful local verification;
final validation, integration, release, version update, commit, and
tag are the Founder's responsibility against the live repository.
