# Implementation Package 021 - Decision Engine

## Objective

Give ArgusOS a first-generation Decision Engine that evaluates one or
more `ReasoningResult` objects (Package 020) against a set of
deterministic rules and produces a structured `Decision` - "It does
not execute decisions. It does not invoke the Planner. It does not
use AI or LLMs. Its responsibility is limited to deterministic
decision evaluation." Per the Founder's Package 021 work order, the
Planner does not consume the Decision Engine yet, and remains
otherwise entirely unchanged; this package only introduces the
service.

```
Conversation -> Memory Service -> Memory Integration -> Knowledge Graph -> Reasoning Engine -> Decision Engine -> Planner -> Validated Plan -> Agent Runtime
```

The Decision Engine is the only component responsible for evaluating
`ReasoningResult` objects against registered rules. It stores nothing
beyond its own rule table; it never mutates memory, the Knowledge
Graph, or anything else, never invokes a Planner, Workflow, Connector,
or LLM.

---

## Specification Note

No `design/specifications/DECISION_ENGINE.md` exists in the
repository - the same situation as Packages 002, 009-020. This
package is built directly from the Founder's explicit work order.

---

## Rule Model

`DecisionRule` (`argus/decision/rule.py`) is an immutable value
object:

```
name: str                                                (required)
predicate: Callable[[Sequence[ReasoningResult]], bool]    (required)
priority: int = 0
id: str = <uuid4>
description: str = ""
```

`predicate` is a plain Python callable, supplied directly by the
caller - never a string of code, a DSL expression, or anything this
module or `DecisionEngine` parses, `eval()`s, `exec()`s, or
dynamically compiles. This package implements no interpreter or
scripting language of any kind: the caller's own Python function IS
the rule; `DecisionRule`/`DecisionEngine` only store it and call it,
deterministically, in priority order. This satisfies "No scripting.
No Python execution. No dynamic code generation" by construction, not
by added validation (see Architectural Decision 1).

Lower `priority` values are evaluated first; ties are broken by
registration order, deterministically (see Architectural Decision 2).

---

## Decision Model

`Decision` (`argus/decision/decision.py`) is an immutable outcome:

```
decision_type: str                                (required)
decision_id: str = <uuid4>
matched_rules: Sequence[DecisionRule] = ()
reasoning_results: Sequence[ReasoningResult] = ()
metadata: Mapping[str, Any] = {}
```

"Decision is immutable." `decision_type` is a caller-supplied,
opaque classification label - the Decision Engine has no domain
knowledge of what any `decision_type` means (see Architectural
Decision 3). `matched_rules` reports every rule that matched, in
priority order; `metadata["rule_evaluations"]` (populated by
`DecisionEngine`) reports a complete matched/not-matched trace for
every registered rule, whether it matched or not.

---

## Engine Architecture

`DecisionEngine` (`argus/decision/engine.py`) implements
`IDecisionEngine` over an injected `IReasoningEngine`:

```
evaluate(reasoning_result, *, decision_type)             -> Decision
evaluate_all(reasoning_results, *, decision_type)         -> Decision
register_rule(rule)                                       -> None
remove_rule(rule_id)                                       -> None
list_rules()                                        -> Sequence[DecisionRule]
decision_summary()                                    -> Mapping[str, Any]
```

- `evaluate()` is a single-`ReasoningResult` convenience that
  delegates to `evaluate_all((reasoning_result,), decision_type=...)`.
- `evaluate_all()` runs every registered rule, in priority order,
  against the full set of `ReasoningResult` objects given - there is
  no "stop at first match" (see Architectural Decision 4). A rule
  whose predicate raises aborts the entire call (see Architectural
  Decision 5).
- `register_rule()`/`remove_rule()`/`list_rules()` are local
  registry operations over this engine's own rule table.
- `decision_summary()` returns a structural snapshot of the
  currently registered rule set (count, and each rule's id/name/
  priority) - not a history of past Decisions, which this package
  does not retain.

---

## Evaluation Lifecycle

```
        caller invokes evaluate() / evaluate_all()
                    |
                    v
        validate input (decision_type, reasoning_results)
           |                        |
      invalid                    valid
           |                        |
           v                        v
    DECISION_FAILED         run every registered rule's
    (raise, no Decision)    predicate, in priority order
                                     |
                     one predicate raises?
                        |                    |
                       yes                   no
                        |                    |
                        v                    v
              DECISION_FAILED         DECISION_EVALUATED
              (raise, no Decision)            |
                                               v
                                    assemble Decision
                                               |
                                               v
                                     DECISION_CREATED
                                               |
                                               v
                                     return Decision
```

Every rule is evaluated even after some have already matched - there
is no early exit. `DECISION_EVALUATED` and `DECISION_CREATED` always
fire together, in that order, on success; `DECISION_FAILED` fires
alone on any failure (invalid input, before any rule runs; or a
raising predicate, aborting mid-evaluation). `register_rule()`/
`remove_rule()` publish nothing at all.

---

## Dependency Graph

```
DecisionEngine
    depends on -> IReasoningEngine   (Package 020; injected, NOT called in Version 1)
    depends on -> IEventBus          (Package 003)

Planner
    remains entirely unchanged; does NOT depend on DecisionEngine yet

AgentRuntime
    does NOT depend on DecisionEngine (unchanged from Package 020)
```

Construction order in `bootstrap.py`: Capability Registry -> Intent
Dispatcher -> Planner -> Knowledge Graph -> Memory Integration ->
Reasoning Engine -> Decision Engine -> Agent Runtime -> Connector
Manager. This is dependency-driven - the third consecutive
dependency-driven core-service placement (after Packages 019 and
020) - since `DecisionEngine` genuinely needs a live
`IReasoningEngine` reference at construction, even though it does not
call any of its methods in Version 1 (see Architectural Decision 6).

---

## Architectural Decisions

### 1. `predicate` is a plain Python callable - no rule scripting language exists in this package

Rather than accepting rule logic as a string expression and writing a
parser/evaluator for it (which would itself be a small scripting
language), `DecisionRule.predicate` is a direct Python callable
supplied by the caller. This satisfies "No scripting. No Python
execution. No dynamic code generation" by construction - there is no
code path anywhere in this package capable of executing arbitrary
text as code.

### 2. Priority ordering: lower first, ties broken by registration order

`list_rules()` and every evaluation sort by `(priority, registration_index)`
ascending - fully deterministic, with no dependence on dict iteration
order or wall-clock time.

### 3. `decision_type` is caller-supplied, opaque data

The Decision Engine has no domain knowledge of what any
`decision_type` string means - it is a classification label the
caller defines and interprets, matching "deterministic infrastructure
only" and this package's own lack of any Responsibility describing
what a `decision_type` should look like.

### 4. `evaluate_all()` runs every rule - no short-circuit on first match

"Explain which rules matched" and `Decision.matched_rules` being
plural both imply the caller wants to know about every match, not
just the first. Running every rule also lets `metadata["rule_evaluations"]`
report a complete trace, satisfying "expose rule evaluation metadata"
directly.

### 5. A raising predicate aborts the call - no best-effort batch

Unlike `MemoryIntegration.synchronize_all()` (Package 019), which
treats individual translation failures as expected and continues the
batch, a `DecisionRule` predicate raising on well-formed input
indicates a bug in the rule itself, not a foreseeable outcome. The
first raising predicate aborts the whole `evaluate_all()` call,
publishes `DECISION_FAILED`, and raises `RuleEvaluationError` - no
partial `Decision` is returned.

### 6. The injected `IReasoningEngine` is wired but not called in Version 1

Per the explicit Bootstrap "Decision Engine depends on: Reasoning
Engine" instruction, `DecisionEngine`'s constructor genuinely accepts
an `IReasoningEngine`. Unlike Package 020's Reasoning Engine (which
genuinely calls its own injected `IMemoryIntegration
.synchronization_status()`), this package does not call any method on
its injected dependency: this package's own Objective describes
`evaluate()`/`evaluate_all()` operating on caller-supplied
`ReasoningResult` objects, never on a live `IReasoningEngine`
reference queried internally, and `IReasoningEngine` has no
zero-argument, whole-system snapshot method comparable to
`IMemoryIntegration.synchronization_status()` that could be attached
blindly. See `argus/decision/interfaces.py`'s own Architectural Note
for the full reasoning, including why this is a third distinct
dependency-usage shape in this codebase (neither Package 018's
"not wired at all" nor Package 020's "wired and genuinely used").

### 7. `IDecisionEngine` inherits `IService`, but zero methods are gated

Per this package's explicit "Create: `IDecisionEngine` - Extending
`IService`" instruction. Applying ADR-0002's criterion independently
to the six actual methods would not have suggested adoption on its
own - all six are synchronous and in-memory, architecturally identical
to Packages 018 and 020. Gated none of them - the fourth zero-gated
case in this codebase. See
`design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md`'s newly
appended Empirical Finding for the full reasoning, including how this
package extends the three-of-four-diverge pattern Package 020's own
finding first identified.

---

## Events

Exactly the three event types this package's own Events section
names: `DECISION_EVALUATED`, `DECISION_CREATED`, `DECISION_FAILED`.
See the Evaluation Lifecycle diagram above for the exact firing
rules. No event exists for `register_rule()`/`remove_rule()` - this
package's own Events section names only these three, all
evaluation-lifecycle.

---

## IService Adoption

`IDecisionEngine` DOES inherit `IService`, per this package's own
explicit work order instruction. Like Packages 018 and 020, and
unlike Package 019, applying ADR-0002's criterion independently to
this package's actual methods would NOT have suggested adoption on
its own - all six public methods are in-memory and ungated. See
Architectural Decision 7 and
`design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md`'s newly
appended Empirical Finding for the full reasoning.

---

## Repository Verification Note

The uploaded repository ("ArgusOS (20).zip") was verified against
this package's own general "verify repository state, verify version
consistency, verify HEAD/tag ancestry, run smoke validation"
pre-flight instruction. Findings: HEAD (`918c91a`, "Synchronize
repository version with v0.2.0 release") is a clean, single-commit
descendant of tag `v0.2.0` (which points to `46ad30d`, "Implement
Package 020 Reasoning Engine"); `v0.1.9` confirmed an ancestor of
HEAD via `git merge-base --is-ancestor`. `git diff v0.1.9..HEAD --stat`
shows exactly the full Package 020 diff (19 files changed) plus the
standard version-sync commit - no anomaly. `git status --short`
showed a completely clean working tree. `argus/reasoning/` (Package
020) present with all expected files; `python -m pytest` passing
(1208 passed, 38 subtests); `python -m unittest discover -s tests`
passing (1120); `python -m unittest discover -s argus/tests` passing
(64); `python main.py` starting and shutting down cleanly (exit 0);
`CORE_SERVICES_VERSION == "0.2.0"` matching tag `v0.2.0`. All
confirmed before any Package 021 code was written.

---

## Files Created

```
argus/
    decision/
        __init__.py
        rule.py
        decision.py
        engine.py
        interfaces.py
        exceptions.py
tests/
    test_decision.py
    test_decision_rule.py
    test_decision_engine.py
```

## Files Modified

```
argus/bootstrap.py            (construct + register Decision Engine
                                as 21st core service, inserted between
                                the Reasoning Engine and the Agent
                                Runtime, per the Bootstrap section's
                                explicit, dependency-driven
                                construction order; CORE_SERVICES_
                                VERSION left at "0.2.0" - not advanced
                                by this package)
argus/events/event_types.py   (3 new event types)
argus/tests/test_bootstrap.py (CORE_SERVICE_NAMES tuple only, per the
                                standing Package 011 rule)
tests/test_bootstrap.py       (CORE_SERVICE_NAMES tuple + 3 new tests)
design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md (Empirical Finding
                                appended; Status remains Proposed)
CHANGELOG.md, DEVLOG.md, IMPLEMENTATION_REPORT.md, factory/ROADMAP.md
```

`argus/reasoning/`, `argus/knowledge_graph/`, `argus/memory_integration/`,
`argus/planner/`, `argus/runtime/`, `argus/dispatcher/`,
`argus/capability/`, `argus/workflow/`, `argus/plugins/`, and
`argus/connectors/` are unchanged - the Decision Engine consumes only
`ReasoningResult`, an existing, unmodified type. Per this package's
own explicit instruction, the Planner remains entirely unchanged and
does not consume the Decision Engine yet.

---

## Test Totals

1,181 tests passing via `python -m unittest discover -s tests` (1,120
from Packages 002-020, plus 7 new in `test_decision.py`, 7 new in
`test_decision_rule.py`, 44 new in `test_decision_engine.py`, and 3
new in `test_bootstrap.py` [38->41]). `python -m unittest discover -s
argus/tests` remains at 64 (duplicate tree unaffected beyond the
standing `CORE_SERVICE_NAMES` sync). `python -m pytest` also passes:
1,269 passed, 38 subtests passed.

---

## Coverage

100% line coverage on every new/modified module measured for this
package: `argus/decision/__init__.py`, `argus/decision/rule.py`,
`argus/decision/decision.py`, `argus/decision/engine.py`,
`argus/decision/interfaces.py`, `argus/decision/exceptions.py`,
`argus/bootstrap.py`, and `argus/events/event_types.py` - all 100%,
no accepted gaps. Overall repository coverage: 99% (unchanged from
Package 020; remaining gaps are pre-existing and out of scope).

---

## Known Limitations

- **No persistence** - `DecisionEngine` retains no history of past
  Decisions; `decision_summary()` reflects only the currently
  registered rule set.
- **No AI, no machine learning, no probabilistic reasoning** - every
  Decision is produced by deterministic, caller-supplied Python
  predicates evaluated in a fixed, documented order.
- **No rule scripting** - predicates are plain Python callables; this
  package implements no interpreter, DSL, or dynamic code execution.
- **A raising predicate aborts the entire evaluation** - there is no
  best-effort, partial-result mode; see Architectural Decision 5.
- **The injected `IReasoningEngine` dependency is not called anywhere
  in Version 1** - wired per the explicit Bootstrap instruction, ready
  for a future package to extend. See Architectural Decision 6.
- **The Planner does not yet consume the Decision Engine** - per this
  package's own explicit Version 1 scope limit and "Planner shall
  remain unchanged" Constraint.
- No concurrency.
- The repository's stray `argus/` duplicate tree (beyond the one
  explicitly-required `test_bootstrap.py` sync) and legacy pre-Factory
  files remain unresolved, out of scope per the Founder's explicit
  repository rules.

---

## Future Expansion

- Wire the Planner to genuinely consult the Decision Engine (the
  diagram already places it directly upstream), once a future
  package's work order explicitly asks for that integration.
- Extend `DecisionEngine` to genuinely query its injected
  `IReasoningEngine` directly, once a concrete requirement for it
  exists - the dependency is already wired for exactly this.
- Consider a bounded or capped rule-evaluation trace if a future
  package's rule sets grow large enough for `metadata["rule_evaluations"]`
  to become unwieldy.
- Revisit whether ADR-0002 should formally separate "adoption"
  (directed or derived) from "gating" (always criterion-driven), per
  this package's own newly appended Empirical Finding.

---

## Release Rules

Per the Founder's explicit instruction: no commit, tag, or push was
performed. `CORE_SERVICES_VERSION` was not changed by this package -
it remains `"0.2.0"`. This package is not reported as complete or
released - implementation ends after successful local verification;
final validation, integration, release, version update, commit, and
tag are the Founder's responsibility against the live repository.
