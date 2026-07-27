# Package 040 — Policy Framework

## Objective

Introduce the Policy domain: "A Policy defines constraints, preferences, or governance that influence future execution." Passive domain objects only — no enforcement, no execution, no policy engine, no AI integration. This package establishes the architecture only.

## Architectural Purpose

Policies answer one question: "Under what rules should Argus operate?" Examples of future policies: human approval required, maximum spending limit, preferred AI model, retry limits, automation permissions, business hours, safety constraints, security requirements. None of these behaviors are implemented yet — Version 1 introduces the passive domain object only.

## New Package

`argus/policy/` — confirmed clear of any collision during pre-flight (unlike Package 039's own `argus/decision/` situation):

```
argus/policy/
    __init__.py
    policy.py
    metadata.py
    builder.py
    status.py
    scope.py
    interfaces.py
    exceptions.py
```

## Policy

Immutable value object. Fields: `policy_id`, `name`, `description`, `status`, `scope`, `metadata` — every field defaults, metadata last, no behavior. `name`/`description` (matching Project/Workspace/Goal's own vocabulary, not DecisionRecord's `title`/`question`) — a Policy's own defining content is a rule or constraint, better captured as a named, described thing.

## PolicyStatus

Plain `Enum`, three members: `ACTIVE`, `INACTIVE`, `ARCHIVED`. No transition logic. `ACTIVE` is the default — matching `WorkspaceStatus`'s own precedent (037), since neither member list names a "not yet begun" state the way `ProjectStatus`/`GoalStatus` do.

## PolicyScope

Plain `Enum`, seven members: `GLOBAL`, `WORKSPACE`, `PROJECT`, `GOAL`, `PLAN`, `TASK`, `CAPABILITY`. "This enum simply describes where a policy may eventually apply. No inheritance or evaluation logic." Member order mirrors this codebase's own organizational hierarchy diagrams (`Workspace -> Project -> Goal -> Plan -> Task`), with `GLOBAL` prepended above `Workspace` and `CAPABILITY` appended below `Task` — presentational only, granting no ordering behavior (verified via `TypeError` on `<`/`>`). `GLOBAL` is the default — a Policy built without an explicit scope is presumed to apply everywhere, the most conservative reading of an unspecified scope.

## PolicyMetadata

Immutable. Fields, in order: `created_at`, `version`, `correlation_id`, `owner`, `tags`, `extra`. "Follow the metadata conventions established by Project, Workspace, Goal, and DecisionRecord" — this package's own work order names the precedent directly for a fourth time (037, 038, and 039 each did the same), leaving no genuine tension between the literal listed order and the established order. `owner`/`tags` remain system-managed, not settable via `PolicyBuilder`, matching every sibling metadata module's identical precedent.

## PolicyBuilder

Mutable fluent builder — the only mutable object. Responsibilities: assign name, assign description, assign status, assign scope, assign metadata, build immutable Policy. `with_scope()` is implemented (unlike `with_owner()`/`with_tags()`), since `scope` is a top-level field and this package's own Responsibilities list names "assign scope" as its own bullet — exactly `GoalBuilder`'s (038) / `DecisionRecordBuilder`'s (039) own reasoning for `priority`. No `with_policy_id()`.

## Integration

No runtime behavior. No Policy Engine. No Planner, Execution, Capability, Bootstrap, Workspace, Project, Goal, Decision, or Response changes. No new core service — `IPolicyBuilder` does not inherit `IService`, mirroring every sibling builder interface in this phase. Introduces the Policy model only.

## Dependency Graph

`policy.py` depends only on `status.py`, `scope.py`, `metadata.py` (all dependency-free leaves). `builder.py` depends on `policy.py`, `status.py`, `scope.py`, `metadata.py`, `exceptions.py`, `interfaces.py`. `argus/policy/` depends on nothing outside itself and the standard library — no import of `argus.decision`, `argus.goal`, `argus.project`, or `argus.workspace`, despite `PolicyScope`'s own member names echoing those packages' own concepts.

## Scope Hierarchy

`GLOBAL` (widest — applies everywhere) → `WORKSPACE` → `PROJECT` → `GOAL` → `PLAN` → `TASK` → `CAPABILITY` (narrowest). Presentational ordering only — `PolicyScope` implements no inheritance (a `GLOBAL`-scoped Policy is not computed to also apply at `WORKSPACE` scope) and no evaluation logic (nothing in this codebase currently checks a Policy's own scope against anything). A future Policy Engine would be the place any such semantics get built.

## Future Governance Model

A Policy may eventually govern: Workspaces, Projects, Goals, Plans, Tasks, Capabilities, Automations, Decision Engine, AI Model Selection, Approval Workflows. Documented only, per this package's own explicit "Do NOT implement them" instruction. No field on `Policy` references any of these in Version 1.

## Real-World Examples

A Policy for Just Tallow: name "Max spend limit," description "Cap automated packaging-vendor spend at $5,000/month without approval," scope `PROJECT`. A Policy for ArgusOS itself: name "Human approval required," description "Require human sign-off before executing high-risk capabilities," scope `CAPABILITY`, status `ACTIVE`.

## Engineering Decisions

1. **`PolicyMetadata`'s field order follows Project/Workspace/Goal/DecisionRecord's identical precedent**, directly named by this package's own work order — a fourth consecutive package to receive this instruction verbatim.
2. **`PolicyStatus` defaults to `ACTIVE`**, matching `WorkspaceStatus`'s own established reasoning (037) rather than `ProjectStatus`'s/`GoalStatus`'s `PLANNING` default, since neither `PolicyStatus`'s nor `WorkspaceStatus`'s own member list names a "not yet begun" state.
3. **`PolicyScope` defaults to `GLOBAL`**, the first-listed member and the most conservative (widest) reading of an unspecified scope — no exception to the "first-listed member is the default" convention was needed here, unlike `GoalPriority`/`DecisionRecordPriority`.
4. **`with_scope()` is implemented; `with_owner()`/`with_tags()` are not** — identical reasoning to `GoalBuilder`/`DecisionRecordBuilder`.
5. **`PolicyScope` member order mirrors the organizational hierarchy but grants it no behavioral significance** — explicitly verified via `TypeError` on ordering comparisons, since `PolicyScope` is a plain `Enum`, not `IntEnum`.

## Repository Verification Note

Uploaded repository ("ArgusOS (39).zip") verified fresh — the twenty-sixth consecutive clean pre-flight (015–040). HEAD (`5ac9136`, "Synchronize repository version with v0.3.9 release") is a clean, single-commit descendant of tag `v0.3.9` (which points to `199a562`, "Implement Package 039 Decision Framework"). `CORE_SERVICES_VERSION == "0.3.9"` matches tag `v0.3.9`. Unlike Package 039, this pre-flight found no naming or path collision — `argus/policy/` did not exist anywhere in the repository prior to this package.

## Files Created

`argus/policy/__init__.py`, `policy.py`, `metadata.py`, `builder.py`, `status.py`, `scope.py`, `interfaces.py`, `exceptions.py`, `factory/packages/040_POLICY_FRAMEWORK.md`, `tests/test_policy.py`, `tests/test_policy_builder.py`, `tests/test_policy_metadata.py`, `tests/test_policy_status.py`, `tests/test_policy_scope.py`.

## Files Modified

`factory/ROADMAP.md`, `CHANGELOG.md`, `DEVLOG.md`, `IMPLEMENTATION_REPORT.md`. `argus/bootstrap.py` and every other existing package are confirmed **unmodified** via `git diff --stat` — this is the fourth package in this phase (after 036, 037, 038) to modify zero pre-existing source or test files, Package 039 being the sole exception in this run for reasons specific to its own naming collision.

## Test Results

New suites: `python -m pytest tests/test_policy*.py -q` → 93 passed. Full suite: `python -m pytest` → 2,723 passed, 38 subtests passed. `python -m unittest discover -s tests` → 2,635 passed. `python -m unittest discover -s argus/tests` → 64 passed, unchanged. `python main.py` → exit 0.

## Coverage

`coverage run --source=argus.policy -m pytest`: 100% across all 8 modules in `argus/policy/` (114 statements).

## Known Limitations

- No governance relationship between `Policy` and any of Workspace/Project/Goal/Plan/Task/Capability/Automations/Decision Engine/AI Model Selection/Approval Workflows is implemented — documented only.
- `owner`/`tags` are not settable through `PolicyBuilder`.
- No transition logic on `PolicyStatus`, no inheritance or evaluation logic on `PolicyScope`.
- No Policy Engine of any kind — nothing in this codebase currently reads, evaluates, or enforces a Policy's own fields.
- No persistence, no concurrency, no scheduling, no runtime behavior of any kind.

## Release Rules

No commits were created. No tags were created. `CORE_SERVICES_VERSION` remains `"0.3.9"`, unchanged. Repository is ready for architectural review.
