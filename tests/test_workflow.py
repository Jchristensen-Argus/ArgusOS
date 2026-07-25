"""Unit tests for argus.workflow.workflow (Workflow, WorkflowStep) and
argus.workflow.state (WorkflowState)."""

import unittest
from datetime import datetime, timezone
from types import MappingProxyType

from argus.workflow import Workflow, WorkflowState, WorkflowStep


class WorkflowStateTests(unittest.TestCase):
    def test_expected_members_exist(self):
        self.assertEqual(
            {member.name for member in WorkflowState},
            {"PENDING", "RUNNING", "COMPLETED", "FAILED", "CANCELLED"},
        )

    def test_members_have_unique_string_values(self):
        values = [member.value for member in WorkflowState]

        self.assertEqual(len(values), len(set(values)))
        self.assertTrue(all(isinstance(v, str) for v in values))


class WorkflowStepTests(unittest.TestCase):
    def test_stores_name_and_action(self):
        action = lambda ctx: ctx

        step = WorkflowStep(name="do-it", action=action)

        self.assertEqual(step.name, "do-it")
        self.assertIs(step.action, action)

    def test_step_is_immutable(self):
        step = WorkflowStep(name="do-it", action=lambda ctx: ctx)

        with self.assertRaises(Exception):
            step.name = "changed"


class WorkflowConstructionTests(unittest.TestCase):
    def _step(self):
        return WorkflowStep(name="s", action=lambda ctx: ctx)

    def test_minimal_construction_defaults(self):
        workflow = Workflow(name="wf", steps=[self._step()])

        self.assertEqual(workflow.name, "wf")
        self.assertEqual(len(workflow.steps), 1)
        self.assertEqual(workflow.state, WorkflowState.PENDING)
        self.assertIsNone(workflow.started_at)
        self.assertIsNone(workflow.completed_at)
        self.assertEqual(workflow.metadata, {})
        self.assertIsInstance(workflow.id, str)
        self.assertTrue(workflow.id)
        self.assertIsInstance(workflow.created_at, datetime)

    def test_id_defaults_are_unique_per_instance(self):
        first = Workflow(name="a", steps=[self._step()])
        second = Workflow(name="b", steps=[self._step()])

        self.assertNotEqual(first.id, second.id)

    def test_created_at_defaults_to_utc_aware_now(self):
        workflow = Workflow(name="wf", steps=[self._step()])

        self.assertIsNotNone(workflow.created_at.tzinfo)
        self.assertEqual(workflow.created_at.tzinfo, timezone.utc)

    def test_explicit_fields_are_honored(self):
        ts = datetime(2026, 1, 1, tzinfo=timezone.utc)
        step = self._step()

        workflow = Workflow(
            name="wf",
            steps=[step],
            id="fixed-id",
            state=WorkflowState.RUNNING,
            created_at=ts,
            started_at=ts,
            completed_at=ts,
            metadata={"key": "value"},
        )

        self.assertEqual(workflow.id, "fixed-id")
        self.assertEqual(workflow.state, WorkflowState.RUNNING)
        self.assertEqual(workflow.created_at, ts)
        self.assertEqual(workflow.started_at, ts)
        self.assertEqual(workflow.completed_at, ts)
        self.assertEqual(workflow.metadata, {"key": "value"})

    def test_multiple_steps_preserve_order(self):
        step_a = WorkflowStep(name="a", action=lambda ctx: ctx)
        step_b = WorkflowStep(name="b", action=lambda ctx: ctx)
        step_c = WorkflowStep(name="c", action=lambda ctx: ctx)

        workflow = Workflow(name="wf", steps=[step_a, step_b, step_c])

        self.assertEqual([s.name for s in workflow.steps], ["a", "b", "c"])


class WorkflowImmutabilityTests(unittest.TestCase):
    def _step(self):
        return WorkflowStep(name="s", action=lambda ctx: ctx)

    def test_workflow_is_frozen(self):
        workflow = Workflow(name="wf", steps=[self._step()])

        with self.assertRaises(Exception):
            workflow.state = WorkflowState.RUNNING

    def test_steps_is_a_tuple_not_the_original_list(self):
        steps_list = [self._step(), self._step()]

        workflow = Workflow(name="wf", steps=steps_list)

        self.assertIsInstance(workflow.steps, tuple)

    def test_mutating_source_steps_list_after_construction_does_not_affect_workflow(self):
        steps_list = [self._step()]
        workflow = Workflow(name="wf", steps=steps_list)

        steps_list.append(self._step())

        self.assertEqual(len(workflow.steps), 1)

    def test_metadata_is_read_only_mapping(self):
        workflow = Workflow(name="wf", steps=[self._step()], metadata={"k": "v"})

        self.assertIsInstance(workflow.metadata, MappingProxyType)
        with self.assertRaises(TypeError):
            workflow.metadata["k"] = "changed"

    def test_mutating_source_metadata_dict_after_construction_does_not_affect_workflow(self):
        source = {"k": "v"}
        workflow = Workflow(name="wf", steps=[self._step()], metadata=source)

        source["k"] = "mutated"

        self.assertEqual(workflow.metadata["k"], "v")


if __name__ == "__main__":
    unittest.main()
