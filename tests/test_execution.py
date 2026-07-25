"""Unit tests for argus.runtime.execution.Execution and
ExecutionStatus."""

import unittest
from datetime import datetime
from types import MappingProxyType

from argus.runtime import Execution, ExecutionStatus


class ExecutionStatusTests(unittest.TestCase):
    def test_all_six_values_exist(self):
        self.assertEqual(ExecutionStatus.CREATED.value, "created")
        self.assertEqual(ExecutionStatus.RUNNING.value, "running")
        self.assertEqual(ExecutionStatus.PAUSED.value, "paused")
        self.assertEqual(ExecutionStatus.FAILED.value, "failed")
        self.assertEqual(ExecutionStatus.COMPLETED.value, "completed")
        self.assertEqual(ExecutionStatus.CANCELLED.value, "cancelled")


class ExecutionConstructionTests(unittest.TestCase):
    def test_minimal_construction(self):
        execution = Execution(plan_id="plan-1")

        self.assertEqual(execution.plan_id, "plan-1")

    def test_id_auto_generated_and_unique(self):
        a = Execution(plan_id="plan-1")
        b = Execution(plan_id="plan-1")

        self.assertTrue(a.id)
        self.assertNotEqual(a.id, b.id)

    def test_explicit_id_honored(self):
        execution = Execution(plan_id="plan-1", id="fixed-id")

        self.assertEqual(execution.id, "fixed-id")

    def test_status_defaults_to_created(self):
        execution = Execution(plan_id="plan-1")

        self.assertEqual(execution.status, ExecutionStatus.CREATED)

    def test_status_honored(self):
        execution = Execution(plan_id="plan-1", status=ExecutionStatus.RUNNING)

        self.assertEqual(execution.status, ExecutionStatus.RUNNING)

    def test_current_step_defaults_to_zero(self):
        execution = Execution(plan_id="plan-1")

        self.assertEqual(execution.current_step, 0)

    def test_current_step_honored(self):
        execution = Execution(plan_id="plan-1", current_step=3)

        self.assertEqual(execution.current_step, 3)

    def test_results_defaults_to_empty(self):
        execution = Execution(plan_id="plan-1")

        self.assertEqual(dict(execution.results), {})

    def test_results_honored(self):
        execution = Execution(plan_id="plan-1", results={"step-1": {"ok": True}})

        self.assertEqual(execution.results["step-1"], {"ok": True})

    def test_started_at_defaults_to_none(self):
        execution = Execution(plan_id="plan-1")

        self.assertIsNone(execution.started_at)

    def test_completed_at_defaults_to_none(self):
        execution = Execution(plan_id="plan-1")

        self.assertIsNone(execution.completed_at)

    def test_started_at_honored(self):
        now = datetime.now()
        execution = Execution(plan_id="plan-1", started_at=now)

        self.assertEqual(execution.started_at, now)

    def test_metadata_defaults_to_empty(self):
        execution = Execution(plan_id="plan-1")

        self.assertEqual(dict(execution.metadata), {})

    def test_metadata_honored(self):
        execution = Execution(plan_id="plan-1", metadata={"source": "package_016"})

        self.assertEqual(execution.metadata["source"], "package_016")


class ExecutionImmutabilityTests(unittest.TestCase):
    def setUp(self):
        self.execution = Execution(
            plan_id="plan-1", results={"k": "v"}, metadata={"k": "v"}
        )

    def test_is_frozen(self):
        with self.assertRaises(Exception):
            self.execution.status = ExecutionStatus.RUNNING

    def test_results_is_mapping_proxy(self):
        self.assertIsInstance(self.execution.results, MappingProxyType)

    def test_results_cannot_be_mutated(self):
        with self.assertRaises(TypeError):
            self.execution.results["k"] = "changed"

    def test_results_immutable_from_source_dict(self):
        source = {"k": "v"}
        execution = Execution(plan_id="plan-1", results=source)
        source["k"] = "changed"

        self.assertEqual(execution.results["k"], "v")

    def test_metadata_is_mapping_proxy(self):
        self.assertIsInstance(self.execution.metadata, MappingProxyType)

    def test_metadata_cannot_be_mutated(self):
        with self.assertRaises(TypeError):
            self.execution.metadata["k"] = "changed"

    def test_metadata_immutable_from_source_dict(self):
        source = {"k": "v"}
        execution = Execution(plan_id="plan-1", metadata=source)
        source["k"] = "changed"

        self.assertEqual(execution.metadata["k"], "v")


if __name__ == "__main__":
    unittest.main()
