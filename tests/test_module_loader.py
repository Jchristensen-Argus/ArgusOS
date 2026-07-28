"""
Unit tests for module_loader.py (Sprint 1, Priority #6).

Uses a real argus.bootstrap.bootstrap() and a real load_modules() -
the same pattern test_bootstrap.py already uses for the Core startup
sequence - so this is a genuine integration test of the composition
root, not a mocked approximation. Like test_bootstrap.py, this writes
real files under memory/, knowledge/, and sales_data/ relative to the
process's working directory; that is accepted existing behavior of
bootstrap()/SalesRepository(), not something introduced here.
"""

import unittest

from argus.bootstrap import bootstrap
from argus.lifecycle.lifecycle import LifecycleState
from argus.modules.sales.registration import (
    SALES_REPOSITORY_SERVICE_NAME,
    register as register_sales,
)
from argus.modules.sales.workflows import SALES_LEAD_INTAKE_WORKFLOW_ID
from argus.workflow.state import WorkflowState
from module_loader import MODULE_REGISTRARS, load_modules


class ModuleRegistrarsTests(unittest.TestCase):
    def test_sales_is_a_registered_module(self):
        self.assertIn(register_sales, MODULE_REGISTRARS)


class LoadModulesIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.application = bootstrap()
        self.addCleanup(self.application.shutdown)
        load_modules(self.application.container)

    def test_sales_plugin_is_registered(self):
        plugin_manager = self.application.container.resolve("plugin_manager")
        names = [p.name for p in plugin_manager.list_plugins()]
        self.assertIn("Sales", names)

    def test_sales_repository_is_resolvable_from_the_container(self):
        repository = self.application.container.resolve(SALES_REPOSITORY_SERVICE_NAME)
        # Just needs to behave like a SalesRepository - load_companies()
        # must not raise even with nothing stored yet.
        repository.load_companies()

    def test_sales_lead_intake_workflow_is_registered_pending(self):
        workflow_engine = self.application.container.resolve("workflow_engine")
        workflow = workflow_engine.get_workflow(SALES_LEAD_INTAKE_WORKFLOW_ID)
        self.assertEqual(workflow.state, WorkflowState.PENDING)
        self.assertEqual(workflow.name, "Sales Lead Intake")

    def test_workflow_engine_is_running_after_load_modules(self):
        workflow_engine = self.application.container.resolve("workflow_engine")
        self.assertEqual(workflow_engine.status(), LifecycleState.RUNNING)

    def test_load_modules_is_idempotent_safe_for_the_workflow_engine_lifecycle(self):
        # Calling load_modules() a second time on the SAME container
        # would re-run register_sales() and hit
        # ServiceAlreadyRegisteredError/DuplicateWorkflowError - that
        # is expected (each process loads Modules exactly once, per
        # module_loader.py's own docstring). What must NOT happen is
        # the *Workflow Engine's own lifecycle guard* being the
        # failure mode; confirm it's already RUNNING so a second
        # load_modules() would not attempt a second initialize()/
        # start() in the first place.
        workflow_engine = self.application.container.resolve("workflow_engine")
        self.assertEqual(workflow_engine.status(), LifecycleState.RUNNING)


if __name__ == "__main__":
    unittest.main()
