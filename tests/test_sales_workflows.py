"""
Unit tests for argus.modules.sales.workflows (Sprint 1, Priority #6).

Covers: the Sales Lead Intake step sequence's shape, and running the
steps directly (bypassing WorkflowEngine) against a real, temp-backed
SalesRepository to verify context evolves correctly step by step.
WorkflowEngine's own execute()/register_workflow() mechanics are
already covered by the Core test suite (test_workflow_engine.py) and
are not re-tested here; test_module_loader.py covers the real
end-to-end path through the Workflow Engine.
"""

import logging
import tempfile
import unittest
from pathlib import Path

from argus.events.event_bus import InMemoryEventBus
from argus.modules.sales.persistence.repository import SalesRepository
from argus.modules.sales.workflows import (
    SALES_LEAD_INTAKE_WORKFLOW_ID,
    build_sales_lead_intake_steps,
)


class StepShapeTests(unittest.TestCase):
    def setUp(self):
        self._tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp_dir.cleanup)
        self.repository = SalesRepository(base_dir=Path(self._tmp_dir.name))

    def test_five_steps_in_expected_order(self):
        steps = build_sales_lead_intake_steps(repository=self.repository)
        self.assertEqual(
            [step.name for step in steps],
            [
                "import_leads",
                "create_work_item_for_first_new_lead",
                "advance_top_work_item",
                "persist_work_queue",
                "summarize",
            ],
        )

    def test_workflow_id_is_a_stable_string(self):
        self.assertEqual(SALES_LEAD_INTAKE_WORKFLOW_ID, "sales_lead_intake")


class StepExecutionTests(unittest.TestCase):
    """Runs the steps directly, in order, exactly as WorkflowEngine
    would - context in, context out - without going through the
    engine itself."""

    def setUp(self):
        self._tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp_dir.cleanup)
        self.repository = SalesRepository(base_dir=Path(self._tmp_dir.name))
        self.bus = InMemoryEventBus(logging.getLogger("test.sales.workflows"))
        self.csv_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.csv_dir.cleanup)

    def _run_all_steps(self, csv_content: str) -> dict:
        csv_path = Path(self.csv_dir.name) / "leads.csv"
        csv_path.write_text(csv_content, encoding="utf-8")
        context = {"csv_path": str(csv_path)}
        steps = build_sales_lead_intake_steps(
            repository=self.repository, event_bus=self.bus
        )
        for step in steps:
            context = step.action(context)
        return context

    def test_import_leads_populates_import_result(self):
        context = self._run_all_steps("Company Name\nAcme\n")
        self.assertEqual(context["import_result"].leads_created, 1)

    def test_a_work_item_is_created_for_the_first_new_lead(self):
        context = self._run_all_steps("Company Name\nAcme\nBeta\n")
        work_item = context["new_work_item"]
        self.assertIsNotNone(work_item)
        first_lead = context["import_result"].leads[0]
        self.assertEqual(work_item.lead_id, first_lead.lead_id)

    def test_the_created_work_item_is_advanced_to_completed(self):
        context = self._run_all_steps("Company Name\nAcme\n")
        completed = context["completed_work_item"]
        self.assertIsNotNone(completed)
        self.assertEqual(completed.work_item_id, context["new_work_item"].work_item_id)
        self.assertEqual(completed.status.value, "completed")

    def test_work_queue_is_persisted_and_resumable(self):
        context = self._run_all_steps("Company Name\nAcme\n")
        completed_id = context["completed_work_item"].work_item_id
        reloaded = self.repository.load_work_items()
        self.assertEqual(len(reloaded), 1)
        self.assertEqual(reloaded[0].work_item_id, completed_id)
        self.assertEqual(reloaded[0].status.value, "completed")

    def test_summary_reflects_the_full_run(self):
        context = self._run_all_steps("Company Name\nAcme\nBeta\n")
        summary = context["summary"]
        self.assertEqual(summary["leads_created"], 2)
        self.assertEqual(summary["companies_created"], 2)
        self.assertTrue(summary["work_item_created"])
        self.assertTrue(summary["work_item_completed"])

    def test_no_new_leads_means_no_work_item_but_no_error(self):
        # A row that fails to parse creates no Lead - the workflow
        # must not error just because there was nothing to queue.
        context = self._run_all_steps("Company Name,Notes\n,missing company\n")
        self.assertIsNone(context["new_work_item"])
        self.assertIsNone(context["completed_work_item"])
        self.assertFalse(context["summary"]["work_item_created"])

    def test_real_events_publish_during_step_execution(self):
        received = []
        from argus.events.event_types import EventType

        self.bus.subscribe(EventType.SALES_MODULE_EVENT, received.append)
        self._run_all_steps("Company Name\nAcme\n")
        event_names = [e.payload["event_name"] for e in received]
        self.assertIn("LeadImported", event_names)
        self.assertIn("WorkItemStarted", event_names)
        self.assertIn("WorkItemCompleted", event_names)


if __name__ == "__main__":
    unittest.main()
