"""Integration tests for Planner.plan_session() (Package 024).

Purpose:
    Verify plan_session() genuinely delegates to the pre-existing
    create_plan()/add_step() methods rather than reimplementing
    planning logic, produces output structurally identical to what
    the legacy API produces for equivalent input, never mutates the
    PlanningSession (or its cognitive_context/goals/constraints) it is
    given, and raises the Planner's own pre-existing InvalidPlanError
    for malformed input - per
    factory/packages/024_PLANNER_SESSION_INTEGRATION.md.
"""

import dataclasses
import logging
import unittest

from argus.capability import CapabilityRegistry
from argus.context import ContextBuilder
from argus.events import EventType, InMemoryEventBus
from argus.intent import Intent, IntentType
from argus.planner import InvalidPlanError, PlanStatus, Planner
from argus.planning import PlanningConstraint, PlanningGoal, PlanningSessionBuilder
from argus.task.builder import TaskBuilder
from argus.task.task import Task


def _silent_logger() -> logging.Logger:
    logger = logging.getLogger("test_planner_session_integration")
    logger.addHandler(logging.NullHandler())
    logger.propagate = False
    return logger


def _step_content(plan):
    """Reduce a Plan's steps to their comparable content, excluding
    the auto-generated `id`, so two independently-constructed Plans
    can be compared for structural equivalence."""
    return [
        (step.description, step.required_capability, step.order, step.optional, dict(step.metadata))
        for step in plan.steps
    ]


class PlannerSessionIntegrationTestCase(unittest.TestCase):
    def setUp(self):
        self.event_bus = InMemoryEventBus(logger=_silent_logger())
        self.capability_registry = CapabilityRegistry(event_bus=self.event_bus)
        self.planner = Planner(
            event_bus=self.event_bus, capability_registry=self.capability_registry
        )
        self.received = []
        for event_type in EventType:
            self.event_bus.subscribe(event_type, self.received.append)


# -- backward compatibility: legacy API untouched ---------------------------


class LegacyApiUnaffectedTests(PlannerSessionIntegrationTestCase):
    def test_create_plan_still_works_exactly_as_before(self):
        intent = Intent(name=IntentType.QUESTION, confidence=0.9)
        plan = self.planner.create_plan(intent)
        self.assertEqual(plan.originating_intent, intent)
        self.assertEqual(plan.status, PlanStatus.CREATED)
        self.assertEqual(plan.steps, ())

    def test_add_step_still_works_exactly_as_before(self):
        plan = self.planner.create_plan(Intent(name=IntentType.COMMAND, confidence=0.5))
        updated = self.planner.add_step(
            plan.id, description="d", required_capability="cap"
        )
        self.assertEqual(len(updated.steps), 1)


# -- empty and populated sessions -------------------------------------------


class EmptySessionTests(PlannerSessionIntegrationTestCase):
    def test_empty_session_produces_plan_with_no_steps(self):
        session = PlanningSessionBuilder().build()
        plan = self.planner.plan_session(session)
        self.assertEqual(plan.steps, ())
        self.assertEqual(plan.status, PlanStatus.CREATED)

    def test_empty_session_metadata_has_no_cognitive_context_id(self):
        session = PlanningSessionBuilder().build()
        plan = self.planner.plan_session(session)
        self.assertNotIn("cognitive_context_id", plan.metadata)

    def test_empty_session_metadata_has_empty_constraints_tuple(self):
        session = PlanningSessionBuilder().build()
        plan = self.planner.plan_session(session)
        self.assertEqual(plan.metadata["constraints"], ())

    def test_empty_session_metadata_carries_session_id(self):
        session = PlanningSessionBuilder().build()
        plan = self.planner.plan_session(session)
        self.assertEqual(plan.metadata["planning_session_id"], session.session_id)

    def test_empty_session_synthesizes_unknown_intent(self):
        session = PlanningSessionBuilder().build()
        plan = self.planner.plan_session(session)
        self.assertEqual(plan.originating_intent.name, IntentType.UNKNOWN)
        self.assertEqual(plan.originating_intent.confidence, 0.0)


class PopulatedSessionTests(PlannerSessionIntegrationTestCase):
    def _session(self):
        context = ContextBuilder().with_conversation("conv-1").build()
        goal_with_description = PlanningGoal(name="cap_a", description="Do A", priority=1)
        goal_without_description = PlanningGoal(name="cap_b", priority=2)
        constraint = PlanningConstraint(name="budget", description="Stay under budget")
        session = (
            PlanningSessionBuilder()
            .with_context(context)
            .with_goal(goal_with_description)
            .with_goal(goal_without_description)
            .with_constraint(constraint)
            .build()
        )
        return context, goal_with_description, goal_without_description, constraint, session

    def test_each_goal_becomes_one_step_in_order(self):
        _, g1, g2, _, session = self._session()
        plan = self.planner.plan_session(session)
        self.assertEqual(len(plan.steps), 2)
        self.assertEqual(plan.steps[0].description, "Do A")
        self.assertEqual(plan.steps[0].required_capability, "cap_a")
        self.assertEqual(plan.steps[0].order, 0)
        self.assertEqual(plan.steps[1].description, "cap_b")
        self.assertEqual(plan.steps[1].required_capability, "cap_b")
        self.assertEqual(plan.steps[1].order, 1)

    def test_goal_without_description_falls_back_to_name(self):
        _, _, g2, _, session = self._session()
        plan = self.planner.plan_session(session)
        self.assertEqual(plan.steps[1].description, g2.name)

    def test_step_metadata_carries_goal_id_and_priority(self):
        _, g1, g2, _, session = self._session()
        plan = self.planner.plan_session(session)
        self.assertEqual(plan.steps[0].metadata["goal_id"], g1.goal_id)
        self.assertEqual(plan.steps[0].metadata["priority"], 1)
        self.assertEqual(plan.steps[1].metadata["goal_id"], g2.goal_id)
        self.assertEqual(plan.steps[1].metadata["priority"], 2)

    def test_step_optional_defaults_to_false(self):
        _, _, _, _, session = self._session()
        plan = self.planner.plan_session(session)
        self.assertFalse(plan.steps[0].optional)
        self.assertFalse(plan.steps[1].optional)

    def test_cognitive_context_id_recorded_in_metadata(self):
        context, _, _, _, session = self._session()
        plan = self.planner.plan_session(session)
        self.assertEqual(plan.metadata["cognitive_context_id"], context.context_id)

    def test_constraint_recorded_descriptively_not_as_step(self):
        _, _, _, constraint, session = self._session()
        plan = self.planner.plan_session(session)
        self.assertEqual(
            plan.metadata["constraints"],
            (
                {
                    "constraint_id": constraint.constraint_id,
                    "name": "budget",
                    "description": "Stay under budget",
                },
            ),
        )
        self.assertEqual(len(plan.steps), 2)  # constraints never become steps


class MultipleGoalsTests(PlannerSessionIntegrationTestCase):
    def test_three_goals_preserve_order(self):
        goals = [PlanningGoal(name=f"cap_{i}", priority=i) for i in range(3)]
        session = PlanningSessionBuilder().with_goal(goals[0]).with_goal(goals[1]).with_goal(goals[2]).build()
        plan = self.planner.plan_session(session)
        self.assertEqual(
            [step.required_capability for step in plan.steps], ["cap_0", "cap_1", "cap_2"]
        )
        self.assertEqual([step.order for step in plan.steps], [0, 1, 2])


class MultipleConstraintsTests(PlannerSessionIntegrationTestCase):
    def test_multiple_constraints_all_recorded(self):
        constraints = [PlanningConstraint(name=f"c{i}") for i in range(3)]
        builder = PlanningSessionBuilder()
        for constraint in constraints:
            builder.with_constraint(constraint)
        session = builder.build()
        plan = self.planner.plan_session(session)
        self.assertEqual(len(plan.metadata["constraints"]), 3)
        self.assertEqual(
            [entry["name"] for entry in plan.metadata["constraints"]], ["c0", "c1", "c2"]
        )
        self.assertEqual(plan.steps, ())  # constraints alone produce no steps


# -- session.tasks carry-through (Package 030) -------------------------


class SessionTasksIntegrationTests(PlannerSessionIntegrationTestCase):
    def test_empty_session_produces_plan_with_no_tasks(self):
        session = PlanningSessionBuilder().build()
        plan = self.planner.plan_session(session)
        self.assertEqual(plan.tasks, ())

    def test_single_task_carried_through_to_plan(self):
        task = TaskBuilder().with_name("t1").build()
        session = PlanningSessionBuilder().with_task(task).build()
        plan = self.planner.plan_session(session)
        self.assertEqual(plan.tasks, (task,))

    def test_multiple_tasks_carried_through_preserving_order(self):
        t1 = TaskBuilder().with_name("t1").build()
        t2 = TaskBuilder().with_name("t2").build()
        t3 = TaskBuilder().with_name("t3").build()
        session = PlanningSessionBuilder().with_tasks([t1, t2, t3]).build()
        plan = self.planner.plan_session(session)
        self.assertEqual(plan.tasks, (t1, t2, t3))

    def test_tasks_carried_through_alongside_goals_and_constraints(self):
        goal = PlanningGoal(name="cap_a")
        constraint = PlanningConstraint(name="budget")
        task = TaskBuilder().with_name("t1").build()
        session = (
            PlanningSessionBuilder()
            .with_goal(goal)
            .with_constraint(constraint)
            .with_task(task)
            .build()
        )
        plan = self.planner.plan_session(session)
        self.assertEqual(plan.tasks, (task,))
        self.assertEqual(len(plan.steps), 1)  # unrelated: goal still becomes a step

    def test_planner_never_generates_tasks_of_its_own(self):
        # plan_session() carries whatever tasks the PlanningSession
        # already has - it never fabricates, decomposes, or derives
        # any Task from goals/constraints.
        session = (
            PlanningSessionBuilder().with_goal(PlanningGoal(name="cap_a")).build()
        )
        plan = self.planner.plan_session(session)
        self.assertEqual(plan.tasks, ())


# -- immutable behavior -------------------------------------------------


class ImmutableBehaviorTests(PlannerSessionIntegrationTestCase):
    def test_session_itself_is_never_mutated(self):
        context = ContextBuilder().with_conversation("c").build()
        goal = PlanningGoal(name="cap_a")
        session = PlanningSessionBuilder().with_context(context).with_goal(goal).build()
        before = dataclasses.replace(session)
        self.planner.plan_session(session)
        self.assertEqual(session, before)

    def test_session_fields_remain_frozen_after_plan_session(self):
        session = PlanningSessionBuilder().with_goal(PlanningGoal(name="cap_a")).build()
        self.planner.plan_session(session)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            session.session_id = "changed"

    def test_goal_remains_frozen_after_plan_session(self):
        goal = PlanningGoal(name="cap_a")
        session = PlanningSessionBuilder().with_goal(goal).build()
        self.planner.plan_session(session)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            goal.name = "changed"

    def test_constraint_remains_frozen_after_plan_session(self):
        constraint = PlanningConstraint(name="c1")
        session = PlanningSessionBuilder().with_constraint(constraint).build()
        self.planner.plan_session(session)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            constraint.name = "changed"

    def test_cognitive_context_remains_frozen_after_plan_session(self):
        context = ContextBuilder().with_conversation("c").build()
        session = PlanningSessionBuilder().with_context(context).build()
        self.planner.plan_session(session)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            context.conversation_id = "changed"

    def test_task_remains_frozen_after_plan_session(self):
        task = TaskBuilder().with_name("t1").build()
        session = PlanningSessionBuilder().with_task(task).build()
        self.planner.plan_session(session)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            task.name = "changed"

    def test_session_tasks_tuple_unaffected_by_plan_session(self):
        task = TaskBuilder().with_name("t1").build()
        session = PlanningSessionBuilder().with_task(task).build()
        before_tasks = session.tasks
        self.planner.plan_session(session)
        self.assertEqual(session.tasks, before_tasks)


# -- delegation path ----------------------------------------------------


class DelegationPathTests(PlannerSessionIntegrationTestCase):
    def test_plan_session_publishes_the_same_events_create_plan_and_add_step_would(self):
        session = (
            PlanningSessionBuilder()
            .with_goal(PlanningGoal(name="cap_a"))
            .with_goal(PlanningGoal(name="cap_b"))
            .build()
        )
        self.planner.plan_session(session)
        event_types = [event.type for event in self.received]
        self.assertEqual(
            event_types,
            [EventType.PLAN_CREATED, EventType.PLAN_UPDATED, EventType.PLAN_UPDATED],
        )

    def test_plan_session_result_is_independently_retrievable_via_get_plan(self):
        # A genuine sign of delegation, not reimplementation: the Plan
        # plan_session() returns was actually registered via
        # create_plan()/add_step()'s own internal `self._plans` store.
        session = PlanningSessionBuilder().with_goal(PlanningGoal(name="cap_a")).build()
        plan = self.planner.plan_session(session)
        retrieved = self.planner.get_plan(plan.id)
        self.assertEqual(retrieved, plan)

    def test_plan_session_result_appears_in_list_plans(self):
        session = PlanningSessionBuilder().build()
        plan = self.planner.plan_session(session)
        self.assertIn(plan, self.planner.list_plans())

    def test_plan_session_result_can_be_validated_like_any_other_plan(self):
        # validate_plan() is untouched by this package; a Plan
        # produced via plan_session() must work with it exactly like
        # any Plan produced via create_plan()/add_step() would.
        session = PlanningSessionBuilder().build()  # no steps -> vacuously validates
        plan = self.planner.plan_session(session)
        validated = self.planner.validate_plan(plan.id)
        self.assertEqual(validated.status, PlanStatus.VALIDATED)


# -- identical output versus legacy API --------------------------------


class IdenticalOutputVersusLegacyApiTests(PlannerSessionIntegrationTestCase):
    def test_plan_session_output_matches_manual_legacy_calls(self):
        context = ContextBuilder().with_conversation("conv-1").build()
        goal_a = PlanningGoal(name="cap_a", description="Do A", priority=1)
        goal_b = PlanningGoal(name="cap_b", priority=2)
        constraint = PlanningConstraint(name="budget", description="Stay under budget")
        session = (
            PlanningSessionBuilder()
            .with_context(context)
            .with_goal(goal_a)
            .with_goal(goal_b)
            .with_constraint(constraint)
            .build()
        )

        via_session = self.planner.plan_session(session)

        # Manually reproduce what plan_session() is documented to do,
        # using only the pre-existing legacy API.
        legacy_intent = Intent(
            name=IntentType.UNKNOWN,
            confidence=0.0,
            parameters={
                "planning_session_id": session.session_id,
                "cognitive_context_id": context.context_id,
            },
        )
        legacy_plan = self.planner.create_plan(
            legacy_intent,
            metadata={
                "planning_session_id": session.session_id,
                "cognitive_context_id": context.context_id,
                "constraints": (
                    {
                        "constraint_id": constraint.constraint_id,
                        "name": "budget",
                        "description": "Stay under budget",
                    },
                ),
            },
        )
        legacy_plan = self.planner.add_step(
            legacy_plan.id,
            description="Do A",
            required_capability="cap_a",
            metadata={"goal_id": goal_a.goal_id, "priority": 1},
        )
        legacy_plan = self.planner.add_step(
            legacy_plan.id,
            description="cap_b",
            required_capability="cap_b",
            metadata={"goal_id": goal_b.goal_id, "priority": 2},
        )

        self.assertEqual(_step_content(via_session), _step_content(legacy_plan))
        self.assertEqual(via_session.status, legacy_plan.status)
        self.assertEqual(dict(via_session.metadata), dict(legacy_plan.metadata))
        self.assertEqual(
            (via_session.originating_intent.name, via_session.originating_intent.confidence),
            (legacy_plan.originating_intent.name, legacy_plan.originating_intent.confidence),
        )

    def test_empty_session_output_matches_manual_legacy_call_with_no_steps(self):
        session = PlanningSessionBuilder().build()
        via_session = self.planner.plan_session(session)

        legacy_intent = Intent(
            name=IntentType.UNKNOWN,
            confidence=0.0,
            parameters={"planning_session_id": session.session_id},
        )
        legacy_plan = self.planner.create_plan(
            legacy_intent,
            metadata={"planning_session_id": session.session_id, "constraints": ()},
        )

        self.assertEqual(_step_content(via_session), _step_content(legacy_plan))
        self.assertEqual(via_session.status, legacy_plan.status)


# -- error handling -------------------------------------------------------


class ErrorHandlingTests(PlannerSessionIntegrationTestCase):
    def test_rejects_non_planning_session_string(self):
        with self.assertRaises(InvalidPlanError):
            self.planner.plan_session("not a session")

    def test_rejects_none(self):
        with self.assertRaises(InvalidPlanError):
            self.planner.plan_session(None)

    def test_rejects_plain_dict_resembling_a_session(self):
        with self.assertRaises(InvalidPlanError):
            self.planner.plan_session({"goals": [], "constraints": []})

    def test_rejects_intent_instance(self):
        # A very deliberate confusion to guard against: passing an
        # Intent (the legacy API's own argument type) to plan_session()
        # must still raise, not silently succeed with wrong semantics.
        with self.assertRaises(InvalidPlanError):
            self.planner.plan_session(Intent(name=IntentType.QUESTION, confidence=0.9))

    def test_failed_validation_does_not_raise_from_plan_session_itself(self):
        # plan_session() itself never calls validate_plan() - a goal
        # whose required_capability is not registered still produces
        # a Plan successfully; only a later, explicit validate_plan()
        # call would fail.
        session = PlanningSessionBuilder().with_goal(PlanningGoal(name="unregistered_cap")).build()
        plan = self.planner.plan_session(session)  # must not raise
        self.assertEqual(len(plan.steps), 1)
        from argus.planner import PlanValidationError

        with self.assertRaises(PlanValidationError):
            self.planner.validate_plan(plan.id)


if __name__ == "__main__":
    unittest.main()
