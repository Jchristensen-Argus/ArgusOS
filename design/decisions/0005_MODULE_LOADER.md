# ADR-0005: The Module Loader (module_loader.py)

## Status

Accepted

---

## Date

2026-07-27

---

## Context

Sprint 1's Sales Module could register a `Plugin` value with `PluginManager` (Package 014) and could construct a real `Workflow` for `WorkflowEngine` (Package 010), but nothing in the repository ever called either registration step for a real, running Argus instance. `argus/modules/sales/plugin.py`'s own module docstring named this gap explicitly and deliberately left it open: "something must still call `plugin_manager.register(build_sales_plugin())` once, at startup... That composition-root addition belongs outside Core."

A dedicated investigation (conducted before the Spreadsheet Importer slice, ahead of this ADR) reviewed the existing bootstrap process, `PluginManager`, and Factory conventions, and confirmed: no discovery/loading mechanism exists anywhere in the repository. `bootstrap.py` is fully static (twenty-six hardcoded Core services). `PluginManager` has zero discovery of its own — registration has always been a caller-initiated, one-at-a-time operation (confirmed via `bootstrap.py`'s own hardcoded registration of a "Core Workflows" built-in `Plugin`). The Factory documents (`design/FACTORY.md`, `factory/workflow.md`) describe engineering process, not runtime loading. That investigation recommended, and explicitly deferred, "a thin Module Loader — hardcoded module list (no dynamic discovery yet), each Module exposes a `register(container)` entry point, loader lives outside `argus/` (repo root, alongside `main.py`) since it must import Modules by construction."

Sprint 1 Priority #6 ("build only enough UI and workflow to prove the complete vertical works end-to-end") is the point that recommendation was deferred until.

## Decision

Implement the Module Loader exactly as recommended, with no changes to the shape:

- **`module_loader.py`** at the repo root (a sibling of `main.py`, never inside `argus/`). `MODULE_REGISTRARS` is a plain, hardcoded tuple of each installed Module's `register(container)` callable — currently `(register_sales,)`. `load_modules(container)` calls each registrar in order, then brings the shared `workflow_engine` Core service to `RUNNING` (`initialize()` then `start()`) if it is not already — done once, by the loader, not by any individual Module, because the Workflow Engine is a shared Core resource multiple Modules may register Workflows with.
- **`argus/modules/sales/registration.py`** — the Sales Module's own `register(container)`. Resolves `plugin_manager`, `event_bus`, and `workflow_engine` from the container; registers the Sales `Plugin`; constructs one `SalesRepository` and registers it in the container as `"sales.repository"` (module-namespaced, reusing the existing `Container` rather than inventing a second lookup mechanism); registers the Sales Lead Intake `Workflow`. Every future Module gets its own `registration.py` following this same shape.
- **`main.py`** calls `load_modules(application.container)` after `bootstrap()`, closing the gap `plugin.py` named.

Explicitly not built:

- **No dynamic discovery.** `MODULE_REGISTRARS` is edited by hand when a Module is added. Sales is still the only Module that exists; building directory-scanning or entry-point discovery for a second Module that doesn't exist yet would be speculative infrastructure.
- **No `IModule` lifecycle abstraction.** A Module's `register(container)` is a plain function, not an interface implementation — matching `WorkflowStep.action`'s and `IIntentRouter`'s registered-handler precedent of "plain callables, no imposed base class."
- **No Command registration.** The original investigation named "Register Commands" as a capability a future loader might need. Inspection at implementation time (`grep` across the full `argus/` tree) confirmed no Command Registry concept exists anywhere in Core as of Sprint 1. Registering against a mechanism that does not exist would mean inventing that mechanism unprompted — out of scope for this ADR, and not requested by anything Sprint 1 needs.

## Consequences

Positive

- Closes the "Open Item" `argus/modules/sales/plugin.py` named in Slice 3 — Sales now fully registers itself (Plugin, services, Workflow) in a real, booted Argus instance, verified via `main.py` and `sales_demo.py`, not merely asserted.
- Preserves CA-10 (Core remains domain-agnostic, permanently): `module_loader.py` imports `argus.modules.sales.registration` by name, but this file sits outside `argus/`, alongside `main.py` — the one place in the whole system allowed to know about both Core and Modules. No file under `argus/` imports anything under `argus/modules/`.
- Establishes the pattern every future Module follows: write a `registration.py` exposing `register(container)`, add it to `MODULE_REGISTRARS`. No other file changes.
- The Workflow Engine's shared lifecycle (`initialize()`/`start()`) is owned by exactly one place (`load_modules()`), preventing a future second Module's `register()` from racing or double-starting it.

Trade-offs

- Module loading remains all-or-nothing and synchronous — a Module whose `register()` raises will abort `load_modules()` for every Module after it in the list. Acceptable for one Module; worth revisiting if and when a second Module's failure shouldn't block a first Module that already succeeded.
- `MODULE_REGISTRARS` being hand-edited is a manual step a future contributor could forget. Named here rather than silently accepted as free of risk.

## Verification

`python3 sales_demo.py` — a real `bootstrap()`, a real `load_modules()`, a real `WorkflowEngine.execute()` against a real CSV — completes with `WorkflowState.COMPLETED`, correctly imports/dedups Leads/Companies/Contacts/Campaigns, creates and completes one `WorkItem`, and persists all of it to `sales_data/`; run twice in sequence, the second run correctly reuses everything the first run created. `python3 main.py` (the real entry point, no demo workflow execution) boots, loads the Sales Module, and shuts down cleanly. `tests/test_module_loader.py` and `tests/test_sales_workflows.py` (15 tests) cover this integration automatically. The full repository suite (2,951 tests + 38 subtests, up from 2,936 before this slice) passes with no regressions.

## Related Documents

- `argus/modules/sales/plugin.py` (the "Open Item" this ADR resolves)
- `argus/modules/sales/registration.py`, `argus/modules/sales/workflows.py`, `module_loader.py`, `sales_demo.py`
- Cognitive Architecture, CA-10 (Core remains domain-agnostic, permanently)
