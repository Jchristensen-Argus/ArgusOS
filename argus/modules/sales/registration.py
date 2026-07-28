"""
The Sales Module's Module Loader entry point (Sprint 1, Priority #6).

Purpose:
    Provide the one function a Module Loader calls to bring the Sales
    Module fully into a running Argus instance: register its Plugin,
    construct its persistence layer, and register its Workflow. This
    is exactly the "Open Item" plugin.py's own module docstring named
    and deliberately left unsolved in Slice 3 ("something must still
    call plugin_manager.register(build_sales_plugin()) once, at
    startup... That composition-root addition belongs outside Core").
    Resolving it now, per the earlier Module Loading investigation's
    recommendation: "each Module exposes a register(container) entry
    point."

Why This Lives Inside argus/modules/sales/, Not In module_loader.py:
    The repo-root Module Loader (module_loader.py) must stay a thin,
    generic loop over a hardcoded list of Modules - it must not know
    Sales's internals (which Plugin, which Workflow, which
    repository). This file is where Sales's OWN wiring logic lives,
    matching the investigation's recommendation exactly: "each Module
    exposes a register(container) entry point." Every future Module
    gets its own registration.py; module_loader.py only ever imports
    and calls each one's register().

What register() Does, In Order:
    1. Builds the Sales Plugin (plugin.py's build_sales_plugin()) and
       registers it with the container's "plugin_manager".
    2. Constructs one SalesRepository (persistence/repository.py) at
       its own default location and registers it in the container as
       "sales.repository" - module-namespaced so it can never collide
       with a Core service name, reusing the Container Core already
       provides rather than inventing a second lookup mechanism.
    3. Builds and registers the Sales Lead Intake Workflow
       (workflows.py) with the container's "workflow_engine", under
       the stable id SALES_LEAD_INTAKE_WORKFLOW_ID.

What register() Deliberately Does Not Do:
    - It does not call workflow_engine.initialize()/start() - the
      Workflow Engine is a shared Core service every Module might
      register a Workflow with; bringing it to RUNNING is
      module_loader.py's responsibility, done once, regardless of how
      many Modules load. One Module's register() owning a shared Core
      service's lifecycle would be exactly the wrong layer for that
      decision.
    - It does not register any Command - no Command Registry exists
      anywhere in Core as of Sprint 1 (confirmed by inspection, not
      assumed); the earlier Module Loading investigation named
      "Register Commands" as a capability a future loader might need,
      not one that exists today. Inventing one now would be exactly
      the unnecessary infrastructure this engagement has consistently
      avoided.

Responsibilities:
    - register(container): the Sales Module's sole Module Loader entry
      point.

Non-Responsibilities:
    - This module does not construct a Container, an IEventBus, a
      PluginManager, or a WorkflowEngine - all are resolved from the
      container supplied by the caller.

Dependencies:
    argus.container (Container - typing only), argus.modules.sales
    (plugin.build_sales_plugin, persistence.SalesRepository,
    workflows.build_sales_lead_intake_steps,
    workflows.SALES_LEAD_INTAKE_WORKFLOW_ID).
"""

from argus.container import Container
from argus.modules.sales.persistence.repository import SalesRepository
from argus.modules.sales.plugin import build_sales_plugin
from argus.modules.sales.workflows import (
    SALES_LEAD_INTAKE_WORKFLOW_ID,
    build_sales_lead_intake_steps,
)

#: The container key the Sales Module's SalesRepository is registered
#: under - module-namespaced (dot-prefixed by module name) so it can
#: never collide with a Core service name, matching the same
#: convention EventType.SALES_MODULE_EVENT established for events.
SALES_REPOSITORY_SERVICE_NAME = "sales.repository"


def register(container: Container) -> None:
    """
    Bring the Sales Module fully into a running Argus instance.

    Parameters:
        container: The already-booted application's Container (i.e.
            application.container after argus.bootstrap.bootstrap()) -
            "plugin_manager", "event_bus", and "workflow_engine" must
            already be registered on it, which bootstrap() guarantees.
    """
    plugin_manager = container.resolve("plugin_manager")
    event_bus = container.resolve("event_bus")
    workflow_engine = container.resolve("workflow_engine")

    plugin_manager.register(build_sales_plugin())

    repository = SalesRepository()
    container.register(SALES_REPOSITORY_SERVICE_NAME, repository)

    workflow_engine.register_workflow(
        name="Sales Lead Intake",
        workflow_id=SALES_LEAD_INTAKE_WORKFLOW_ID,
        steps=build_sales_lead_intake_steps(repository=repository, event_bus=event_bus),
        metadata={"module": "sales", "sprint": 1},
    )
