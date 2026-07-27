"""Unit tests for argus.planner.planner.Planner."""

import logging
import unittest

from argus.capability import Capability, CapabilityRegistry
from argus.events import EventType, InMemoryEventBus
from argus.intent import Intent, IntentType
from argus.planner import (
    InvalidPlanError,
    IPlanner,
    PlanNotFoundError,
    PlanStatus,
    PlanValidationError,
    Planner,
    StepNotFoundError,
)
from argus.task.builder import TaskBuilder
from argus.task.task import Task


def _silent_logger() -> logging.Logger:
    logger = logging.getLogger("test_planner")
    logger.addHandler(logging.NullHandler())
    logger.propagate = False
    return logger


def _intent(**overrides):
    defaults = dict(name=IntentType.QUESTION, confidence=0.9)
    defaults.update(overrides)
    return Intent(**defaults)


def _capability(**overrides):
    defaults = dict(
        name="Answer",
        description="Answers questions.",
        intent_types=[IntentType.QUESTION],
        action_kind="workflow",
        workflow_id="answer_workflow",
    )
    defaults.update(overrides)
    return Capability(**defaults)


class PlannerTestCase(unittest.TestCase):
    def setUp(self):
        self.event_bus = InMemoryEventBus(logger=_silent_logger())
        self.capability_registry = CapabilityRegistry(event_bus=self.event_bus)
        self.planner = Planner(
            event_bus=self.event_bus, capability_registry=self.capability_registry
        )
        self.received = []
        for event_type in EventType:
            self.event_bus.subscribe(event_type, self.received.append)

    def _registered_capability(self, **overrides) -> Capability:
        capability = _capability(**overrides)
        self.capability_registry.register(capability)
        return capability


# -- interface / not-an-IService ------------------------------------------


class PlannerIdentityTests(unittest.TestCase):
    def _planner(self):
        bus = InMemoryEventBus(logger=_silent_logger())
        return Planner(event_bus=bus, capability_registry=CapabilityRegistry(event_bus=bus))

    def test_is_an_iplanner(self):
        self.assertIsInstance(self._planner(), IPlanner)

    def test_is_not_an_iservice(self):
        # Deliberate: Planner does not adopt IService - see
        # argus/planner/interfaces.py's Architectural Note.
        from argus.lifecycle import IService

        self.assertNotIsInstance(self._planner(), IService)

    def test_all_planner_methods_available_immediately(self):
        # No lifecycle to initialize/start - every method works the
        # instant the Planner is constructed.
        planner = self._planner()
        plan = planner.create_plan(_intent())  # must not raise
        self.assertEqual(planner.get_plan(plan.id).id, plan.id)


# -- create_plan() -----------------------------------------------------------


class CreatePlanTests(PlannerTestCase):
    def test_creates_plan_with_created_status(self):
        plan = self.planner.create_plan(_intent())

        self.assertEqual(plan.status, PlanStatus.CREATED)
        self.assertEqual(plan.steps, ())

    def test_makes_plan_discoverable(self):
        plan = self.planner.create_plan(_intent())

        self.assertIn(plan, self.planner.list_plans())
        self.assertEqual(self.planner.get_plan(plan.id).id, plan.id)

    def test_rejects_non_intent(self):
        with self.assertRaises(InvalidPlanError):
            self.planner.create_plan("not an intent")

    def test_stores_originating_intent(self):
        intent = _intent()
        plan = self.planner.create_plan(intent)

        self.assertIs(plan.originating_intent, intent)

    def test_honors_metadata(self):
        plan = self.planner.create_plan(_intent(), metadata={"source": "test"})

        self.assertEqual(plan.metadata["source"], "test")

    def test_publishes_plan_created(self):
        plan = self.planner.create_plan(_intent())

        events = [e for e in self.received if e.type == EventType.PLAN_CREATED]
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].payload["plan_id"], plan.id)

    def test_failed_create_does_not_publish(self):
        with self.assertRaises(InvalidPlanError):
            self.planner.create_plan(object())

        self.assertEqual(self.received, [])


# -- create_plan() tasks (Package 030) ----------------------------------------


class CreatePlanTasksTests(PlannerTestCase):
    def test_tasks_default_to_empty_tuple(self):
        plan = self.planner.create_plan(_intent())

        self.assertEqual(plan.tasks, ())

    def test_honors_single_task(self):
        task = TaskBuilder().with_name("t1").build()

        plan = self.planner.create_plan(_intent(), tasks=[task])

        self.assertEqual(plan.tasks, (task,))

    def test_honors_multiple_tasks_preserving_insertion_order(self):
        t1 = TaskBuilder().with_name("t1").build()
        t2 = TaskBuilder().with_name("t2").build()
        t3 = TaskBuilder().with_name("t3").build()

        plan = self.planner.create_plan(_intent(), tasks=[t1, t2, t3])

        self.assertEqual(plan.tasks, (t1, t2, t3))

    def test_tasks_wrapped_in_tuple(self):
        task = TaskBuilder().with_name("t1").build()

        plan = self.planner.create_plan(_intent(), tasks=[task])

        self.assertIsInstance(plan.tasks, tuple)

    def test_rejects_duplicate_task_id(self):
        task = TaskBuilder().with_name("t1").build()
        duplicate = Task(task_id=task.task_id, name="different-name")

        with self.assertRaises(InvalidPlanError):
            self.planner.create_plan(_intent(), tasks=[task, duplicate])

    def test_rejects_non_task_item(self):
        with self.assertRaises(InvalidPlanError):
            self.planner.create_plan(_intent(), tasks=["not a task"])

    def test_rejects_non_list_or_tuple(self):
        with self.assertRaises(InvalidPlanError):
            self.planner.create_plan(_intent(), tasks="not a list")

    def test_accepts_tuple_of_tasks(self):
        t1 = TaskBuilder().with_name("t1").build()
        t2 = TaskBuilder().with_name("t2").build()

        plan = self.planner.create_plan(_intent(), tasks=(t1, t2))

        self.assertEqual(plan.tasks, (t1, t2))

    def test_does_not_generate_tasks_automatically(self):
        # Planner never creates Tasks on its own - create_plan()
        # without a tasks= argument produces an empty tasks tuple,
        # exactly like its pre-030 default.
        plan = self.planner.create_plan(_intent())

        self.assertEqual(plan.tasks, ())

    def test_failed_task_validation_does_not_store_plan(self):
        task = TaskBuilder().with_name("t1").build()
        duplicate = Task(task_id=task.task_id, name="different-name")

        with self.assertRaises(InvalidPlanError):
            self.planner.create_plan(_intent(), tasks=[task, duplicate])

        self.assertEqual(self.planner.list_plans(), ())

    def test_failed_task_validation_does_not_publish(self):
        task = TaskBuilder().with_name("t1").build()
        duplicate = Task(task_id=task.task_id, name="different-name")

        with self.assertRaises(InvalidPlanError):
            self.planner.create_plan(_intent(), tasks=[task, duplicate])

        self.assertEqual(self.received, [])


# -- add_step() ---------------------------------------------------------------


class AddStepTests(PlannerTestCase):
    def test_appends_step_with_correct_order(self):
        plan = self.planner.create_plan(_intent())

        plan = self.planner.add_step(plan.id, description="A", required_capability="cap-1")
        plan = self.planner.add_step(plan.id, description="B", required_capability="cap-2")

        self.assertEqual([s.order for s in plan.steps], [0, 1])
        self.assertEqual([s.description for s in plan.steps], ["A", "B"])

    def test_rejects_unknown_plan_id(self):
        with self.assertRaises(PlanNotFoundError):
            self.planner.add_step("missing", description="A", required_capability="cap-1")

    def test_rejects_non_string_plan_id(self):
        with self.assertRaises(InvalidPlanError):
            self.planner.add_step(123, description="A", required_capability="cap-1")

    def test_rejects_empty_description(self):
        plan = self.planner.create_plan(_intent())

        with self.assertRaises(InvalidPlanError):
            self.planner.add_step(plan.id, description="", required_capability="cap-1")

    def test_rejects_empty_required_capability(self):
        plan = self.planner.create_plan(_intent())

        with self.assertRaises(InvalidPlanError):
            self.planner.add_step(plan.id, description="A", required_capability="")

    def test_honors_optional_flag(self):
        plan = self.planner.create_plan(_intent())

        plan = self.planner.add_step(
            plan.id, description="A", required_capability="cap-1", optional=True
        )

        self.assertTrue(plan.steps[0].optional)

    def test_resets_status_to_created_after_validation(self):
        capability = self._registered_capability(id="cap-1")
        plan = self.planner.create_plan(_intent())
        plan = self.planner.add_step(plan.id, description="A", required_capability=capability.id)
        plan = self.planner.validate_plan(plan.id)
        self.assertEqual(plan.status, PlanStatus.VALIDATED)

        plan = self.planner.add_step(plan.id, description="B", required_capability="cap-2")

        self.assertEqual(plan.status, PlanStatus.CREATED)

    def test_publishes_plan_updated(self):
        plan = self.planner.create_plan(_intent())
        self.received.clear()

        plan = self.planner.add_step(plan.id, description="A", required_capability="cap-1")

        events = [e for e in self.received if e.type == EventType.PLAN_UPDATED]
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].payload["plan_id"], plan.id)
        self.assertEqual(events[0].payload["change"], "added_step")

    def test_failed_add_does_not_publish(self):
        plan = self.planner.create_plan(_intent())
        self.received.clear()

        with self.assertRaises(InvalidPlanError):
            self.planner.add_step(plan.id, description="", required_capability="cap-1")

        self.assertEqual(self.received, [])


# -- remove_step() --------------------------------------------------------


class RemoveStepTests(PlannerTestCase):
    def setUp(self):
        super().setUp()
        plan = self.planner.create_plan(_intent())
        plan = self.planner.add_step(plan.id, description="A", required_capability="cap-1")
        plan = self.planner.add_step(plan.id, description="B", required_capability="cap-2")
        self.plan = self.planner.add_step(
            plan.id, description="C", required_capability="cap-3"
        )

    def test_removes_step(self):
        step_id = self.plan.steps[1].id

        plan = self.planner.remove_step(self.plan.id, step_id)

        self.assertEqual([s.description for s in plan.steps], ["A", "C"])

    def test_renumbers_remaining_steps(self):
        step_id = self.plan.steps[0].id

        plan = self.planner.remove_step(self.plan.id, step_id)

        self.assertEqual([s.order for s in plan.steps], [0, 1])

    def test_rejects_unknown_step_id(self):
        with self.assertRaises(StepNotFoundError):
            self.planner.remove_step(self.plan.id, "missing-step")

    def test_rejects_non_string_step_id(self):
        with self.assertRaises(InvalidPlanError):
            self.planner.remove_step(self.plan.id, 123)

    def test_rejects_unknown_plan_id(self):
        with self.assertRaises(PlanNotFoundError):
            self.planner.remove_step("missing-plan", self.plan.steps[0].id)

    def test_resets_status_to_created(self):
        # Package 033: CapabilityRegistry now rejects duplicate names,
        # not just duplicate ids - each of these three needs its own
        # distinct name, since they previously all shared _capability()'s
        # own default name ("Answer").
        self.capability_registry.register(_capability(id="cap-1", name="Answer 1"))
        self.capability_registry.register(_capability(id="cap-2", name="Answer 2"))
        self.capability_registry.register(_capability(id="cap-3", name="Answer 3"))
        validated = self.planner.validate_plan(self.plan.id)
        self.assertEqual(validated.status, PlanStatus.VALIDATED)

        plan = self.planner.remove_step(self.plan.id, self.plan.steps[0].id)

        self.assertEqual(plan.status, PlanStatus.CREATED)

    def test_publishes_plan_updated(self):
        step_id = self.plan.steps[0].id
        self.received.clear()

        self.planner.remove_step(self.plan.id, step_id)

        events = [e for e in self.received if e.type == EventType.PLAN_UPDATED]
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].payload["change"], "removed_step")
        self.assertEqual(events[0].payload["step_id"], step_id)

    def test_failed_remove_does_not_publish(self):
        self.received.clear()

        with self.assertRaises(StepNotFoundError):
            self.planner.remove_step(self.plan.id, "missing-step")

        self.assertEqual(self.received, [])


# -- reorder_steps() -------------------------------------------------------


class ReorderStepsTests(PlannerTestCase):
    def setUp(self):
        super().setUp()
        plan = self.planner.create_plan(_intent())
        plan = self.planner.add_step(plan.id, description="A", required_capability="cap-1")
        plan = self.planner.add_step(plan.id, description="B", required_capability="cap-2")
        self.plan = self.planner.add_step(
            plan.id, description="C", required_capability="cap-3"
        )
        self.ids = [s.id for s in self.plan.steps]

    def test_reorders_steps(self):
        new_order = [self.ids[2], self.ids[0], self.ids[1]]

        plan = self.planner.reorder_steps(self.plan.id, new_order)

        self.assertEqual([s.id for s in plan.steps], new_order)

    def test_reassigns_order_fields(self):
        new_order = list(reversed(self.ids))

        plan = self.planner.reorder_steps(self.plan.id, new_order)

        self.assertEqual([s.order for s in plan.steps], [0, 1, 2])

    def test_rejects_missing_step_id(self):
        with self.assertRaises(InvalidPlanError):
            self.planner.reorder_steps(self.plan.id, self.ids[:2])

    def test_rejects_unknown_step_id(self):
        with self.assertRaises(InvalidPlanError):
            self.planner.reorder_steps(self.plan.id, self.ids[1:] + ["unknown-id"])

    def test_rejects_duplicate_step_id(self):
        with self.assertRaises(InvalidPlanError):
            self.planner.reorder_steps(self.plan.id, [self.ids[0], self.ids[0], self.ids[1]])

    def test_rejects_unknown_plan_id(self):
        with self.assertRaises(PlanNotFoundError):
            self.planner.reorder_steps("missing-plan", self.ids)

    def test_resets_status_to_created(self):
        # Package 033: CapabilityRegistry now rejects duplicate names,
        # not just duplicate ids - each of these three needs its own
        # distinct name, since they previously all shared _capability()'s
        # own default name ("Answer").
        self.capability_registry.register(_capability(id="cap-1", name="Answer 1"))
        self.capability_registry.register(_capability(id="cap-2", name="Answer 2"))
        self.capability_registry.register(_capability(id="cap-3", name="Answer 3"))
        validated = self.planner.validate_plan(self.plan.id)
        self.assertEqual(validated.status, PlanStatus.VALIDATED)

        plan = self.planner.reorder_steps(self.plan.id, list(reversed(self.ids)))

        self.assertEqual(plan.status, PlanStatus.CREATED)

    def test_publishes_plan_updated(self):
        self.received.clear()

        self.planner.reorder_steps(self.plan.id, list(reversed(self.ids)))

        events = [e for e in self.received if e.type == EventType.PLAN_UPDATED]
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].payload["change"], "reordered")

    def test_failed_reorder_does_not_publish(self):
        self.received.clear()

        with self.assertRaises(InvalidPlanError):
            self.planner.reorder_steps(self.plan.id, self.ids[:2])

        self.assertEqual(self.received, [])


# -- validate_plan() -------------------------------------------------------


class ValidatePlanTests(PlannerTestCase):
    def test_empty_plan_validates_vacuously(self):
        plan = self.planner.create_plan(_intent())

        validated = self.planner.validate_plan(plan.id)

        self.assertEqual(validated.status, PlanStatus.VALIDATED)

    def test_validates_when_required_capability_exists(self):
        capability = self._registered_capability(id="cap-1")
        plan = self.planner.create_plan(_intent())
        plan = self.planner.add_step(plan.id, description="A", required_capability=capability.id)

        validated = self.planner.validate_plan(plan.id)

        self.assertEqual(validated.status, PlanStatus.VALIDATED)

    def test_fails_when_required_capability_missing(self):
        plan = self.planner.create_plan(_intent())
        plan = self.planner.add_step(plan.id, description="A", required_capability="does-not-exist")

        with self.assertRaises(PlanValidationError):
            self.planner.validate_plan(plan.id)

    def test_failed_validation_persists_failed_status(self):
        plan = self.planner.create_plan(_intent())
        plan = self.planner.add_step(plan.id, description="A", required_capability="does-not-exist")

        with self.assertRaises(PlanValidationError):
            self.planner.validate_plan(plan.id)

        self.assertEqual(self.planner.get_plan(plan.id).status, PlanStatus.FAILED)

    def test_optional_step_missing_capability_does_not_fail_validation(self):
        plan = self.planner.create_plan(_intent())
        plan = self.planner.add_step(
            plan.id, description="A", required_capability="does-not-exist", optional=True
        )

        validated = self.planner.validate_plan(plan.id)

        self.assertEqual(validated.status, PlanStatus.VALIDATED)

    def test_never_invokes_capability_registry_beyond_contains(self):
        # Planner's only touchpoint is a read-only contains() check -
        # it never calls register()/unregister()/get() on the
        # injected registry itself.
        capability = self._registered_capability(id="cap-1")
        plan = self.planner.create_plan(_intent())
        plan = self.planner.add_step(plan.id, description="A", required_capability=capability.id)

        self.planner.validate_plan(plan.id)

        # The capability is untouched - still present, unchanged.
        self.assertIs(self.capability_registry.get(capability.id), capability)

    def test_rejects_unknown_plan_id(self):
        with self.assertRaises(PlanNotFoundError):
            self.planner.validate_plan("missing")

    def test_rejects_non_string_plan_id(self):
        with self.assertRaises(InvalidPlanError):
            self.planner.validate_plan(123)

    def test_publishes_plan_validated_on_success(self):
        plan = self.planner.create_plan(_intent())
        self.received.clear()

        self.planner.validate_plan(plan.id)

        events = [e for e in self.received if e.type == EventType.PLAN_VALIDATED]
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].payload["plan_id"], plan.id)

    def test_failed_validation_does_not_publish_plan_validated(self):
        plan = self.planner.create_plan(_intent())
        plan = self.planner.add_step(plan.id, description="A", required_capability="does-not-exist")
        self.received.clear()

        with self.assertRaises(PlanValidationError):
            self.planner.validate_plan(plan.id)

        events = [e for e in self.received if e.type == EventType.PLAN_VALIDATED]
        self.assertEqual(events, [])


# -- get_plan() -------------------------------------------------------------


class GetPlanTests(PlannerTestCase):
    def test_returns_registered_plan(self):
        plan = self.planner.create_plan(_intent())

        self.assertEqual(self.planner.get_plan(plan.id).id, plan.id)

    def test_rejects_non_string(self):
        with self.assertRaises(InvalidPlanError):
            self.planner.get_plan(123)

    def test_rejects_unknown_id(self):
        with self.assertRaises(PlanNotFoundError):
            self.planner.get_plan("missing")


# -- list_plans() -------------------------------------------------------------


class ListPlansTests(PlannerTestCase):
    def test_empty_by_default(self):
        self.assertEqual(self.planner.list_plans(), ())

    def test_returns_all_plans_in_creation_order(self):
        first = self.planner.create_plan(_intent())
        second = self.planner.create_plan(_intent())

        self.assertEqual(
            [p.id for p in self.planner.list_plans()], [first.id, second.id]
        )

    def test_does_not_publish_events(self):
        self.planner.create_plan(_intent())
        self.received.clear()

        self.planner.list_plans()

        self.assertEqual(self.received, [])


if __name__ == "__main__":
    unittest.main()
