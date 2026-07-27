# Package 041 — Automation Framework

## Objective

Introduce the Automation domain: "An Automation defines what should run, when it should run, and under what conditions. It is a passive definition only." "No scheduler or execution engine belongs in this package." Per the Founder's own accompanying note, this is intended as the last foundational package before a full architecture review.

## New Package

`argus/automation/` — confirmed clear of any collision during pre-flight, matching Package 040's own clean situation rather than Package 039's own naming conflict:

```
argus/automation/
    __init__.py
    automation.py
    metadata.py
    builder.py
    status.py
    trigger.py
    interfaces.py
    exceptions.py
```

## Automation

Immutable value object. Fields: `automation_id`, `name`, `description`, `status`, `trigger`, `metadata` — every field defaults, metadata last, no behavior. `name`/`description` matches Project/Workspace/Goal/Policy's own vocabulary.

## AutomationStatus

Plain `Enum`, four members: `ACTIVE`, `PAUSED`, `DISABLED`, `ARCHIVED`. No transition logic. `ACTIVE` is the default — matching `PolicyStatus`'s (040) / `WorkspaceStatus`'s (037) own precedent, since neither this member list nor those name a "not yet begun" state.

## AutomationTrigger

Plain `Enum`, four members: `MANUAL`, `SCHEDULE`, `EVENT`, `CONDITION`. "This identifies how an automation may eventually start. Do not implement scheduling, event handling, or condition evaluation." `MANUAL` is the default — the first-listed member, and independently the most conservative reading of an unspecified trigger (no autonomous behavior implied by default). Unlike `GoalPriority`/`DecisionRecordPriority`, no deliberate override of the "first-listed member is the default" convention was needed here, since the safest choice and the first-listed choice happen to coincide.

## AutomationMetadata

Immutable. Fields, in order: `created_at`, `version`, `correlation_id`, `owner`, `tags`, `extra`. "Follow the established metadata convention" — the least specific phrasing of this instruction yet (037-040 each named specific prior packages), but by this point in the codebase's own history there is only one established convention left: five consecutive sibling metadata modules (`ProjectMetadata` 036, `WorkspaceMetadata` 037, `GoalMetadata` 038, `DecisionRecordMetadata` 039, `PolicyMetadata` 040) all agree on the identical six-field order. `AutomationMetadata` follows it a sixth time. `owner`/`tags` remain system-managed, not settable via `AutomationBuilder`.

## AutomationBuilder

Mutable fluent builder — the only mutable object. Responsibilities: assign name, assign description, assign status, assign trigger, assign metadata, build immutable Automation. `with_trigger()` is implemented (unlike `with_owner()`/`with_tags()`), since `trigger` is a top-level field and this package's own Responsibilities list names "assign trigger" as its own bullet — the same reasoning `PolicyBuilder`'s (040) `with_scope()` and `GoalBuilder`'s/`DecisionRecordBuilder`'s (038, 039) `with_priority()` already established. No `with_automation_id()`.

## Integration

No runtime behavior. No scheduler. No automation engine. No Planner, Capability, Bootstrap, or Execution changes. No new core service — `IAutomationBuilder` does not inherit `IService`, mirroring every sibling builder interface in this phase. Introduces the Automation model only.

## Dependency Graph

`automation.py` depends only on `status.py`, `trigger.py`, `metadata.py` (all dependency-free leaves). `builder.py` depends on `automation.py`, `status.py`, `trigger.py`, `metadata.py`, `exceptions.py`, `interfaces.py`. `argus/automation/` depends on nothing outside itself and the standard library — no import of `argus.policy`, `argus.decision`, `argus.goal`, `argus.project`, or `argus.workspace`, despite this package's own Future Relationship section naming all of them.

## Lifecycle Overview

`AutomationStatus` describes an Automation's own current standing (`ACTIVE` → `PAUSED`/`DISABLED` → `ARCHIVED`, with no transition logic enforcing any particular path). `AutomationTrigger` describes how an Automation would eventually be invoked, independent of its status — a `PAUSED` Automation still carries whatever `AutomationTrigger` it was built with, it simply isn't currently running. Neither enum implements or references any actual scheduling, dispatch, or evaluation mechanism; both are purely descriptive labels on an otherwise inert value object.

## Future Relationship

An Automation may eventually reference: Policies, Capabilities, Workspaces, Projects, Goals, Plans, Tasks, DecisionRecord, Events, Schedules. Documented only, per this package's own explicit instruction. No field on `Automation` references any of these in Version 1.

## Real-World Examples

An Automation for Just Tallow: name "Nightly sales report," description "Compile and email the previous day's sales figures," trigger `SCHEDULE`, status `ACTIVE`. An Automation for ArgusOS itself: name "Manual dependency audit," description "Human-triggered review of outdated dependencies," trigger `MANUAL`, status `PAUSED`.

## Engineering Decisions

1. **`AutomationMetadata`'s field order follows the now-settled six-field convention**, per the least-specific-yet phrasing of this instruction — no genuine tension, since five prior sibling metadata modules already agree exactly.
2. **`AutomationStatus` defaults to `ACTIVE`**, matching `PolicyStatus`/`WorkspaceStatus` rather than `ProjectStatus`/`GoalStatus`, for the identical reason: no "not yet begun" member exists in this list.
3. **`AutomationTrigger` defaults to `MANUAL`** — the first-listed member and the most conservative choice simultaneously, requiring no deliberate override of the standard convention.
4. **`with_trigger()` is implemented; `with_owner()`/`with_tags()` are not** — identical reasoning to `PolicyBuilder`/`GoalBuilder`/`DecisionRecordBuilder`.

## Repository Verification Note

Uploaded repository ("ArgusOS (40).zip") verified fresh — the twenty-seventh consecutive clean pre-flight (015–041). HEAD (`43041f3`, "Synchronize repository version with v0.4.0 release") is a clean, single-commit descendant of tag `v0.4.0` (which points to `cd3eeaa`, "Implement Package 040 Policy Framework"). `CORE_SERVICES_VERSION == "0.4.0"` matches tag `v0.4.0` — a minor version bump rather than a patch increment, the Founder's own release choice, not something this package's own implementation altered or needs to account for. No naming or path collision — `argus/automation/` did not exist anywhere in the repository prior to this package.

## Files Created

`argus/automation/__init__.py`, `automation.py`, `metadata.py`, `builder.py`, `status.py`, `trigger.py`, `interfaces.py`, `exceptions.py`, `factory/packages/041_AUTOMATION_FRAMEWORK.md`, `tests/test_automation.py`, `tests/test_automation_builder.py`, `tests/test_automation_metadata.py`, `tests/test_automation_status.py`, `tests/test_automation_trigger.py`.

## Files Modified

`factory/ROADMAP.md`, `CHANGELOG.md`, `DEVLOG.md`, `IMPLEMENTATION_REPORT.md`. `argus/bootstrap.py` and every other existing package are confirmed **unmodified** via `git diff --stat` — the fifth package in this phase (after 036, 037, 038, 040) to modify zero pre-existing source or test files.

## Test Results

New suites: `python -m pytest tests/test_automation*.py -q` → 93 passed. Full suite: `python -m pytest` → 2,816 passed, 38 subtests passed. `python -m unittest discover -s tests` → 2,728 passed. `python -m unittest discover -s argus/tests` → 64 passed, unchanged. `python main.py` → exit 0.

## Coverage

`coverage run --source=argus.automation -m pytest`: 100% across all 8 modules in `argus/automation/` (112 statements).

## Known Limitations

- No relationship between `Automation` and any of Policies/Capabilities/Workspaces/Projects/Goals/Plans/Tasks/DecisionRecord/Events/Schedules is implemented — documented only.
- `owner`/`tags` are not settable through `AutomationBuilder`.
- No transition logic on `AutomationStatus`, no scheduling/event/condition logic behind `AutomationTrigger`.
- No scheduler, no automation engine, no execution of any kind — an Automation, once built, does nothing.
- No persistence, no concurrency, no runtime behavior of any kind.

## Release Rules

No commits were created. No tags were created. `CORE_SERVICES_VERSION` remains `"0.4.0"`, unchanged. Repository is ready for architectural review — per the Founder's own note, this is intended as the pause point for a full review of the foundational packages built across this phase (036–041).
