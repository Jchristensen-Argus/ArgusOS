"""Unit tests for argus.planning.builder.PlanningSessionBuilder."""

import unittest

from argus.context.context import CognitiveContext
from argus.planning.builder import PlanningSessionBuilder
from argus.planning.constraint import PlanningConstraint
from argus.planning.exceptions import InvalidPlanningSessionError
from argus.planning.goal import PlanningGoal
from argus.planning.interfaces import IPlanningSessionBuilder
from argus.planning.session import PlanningSession
from argus.task.builder import TaskBuilder
from argus.task.task import Task


class PlanningSessionBuilderInterfaceTests(unittest.TestCase):
    def test_builder_implements_interface(self):
        self.assertIsInstance(PlanningSessionBuilder(), IPlanningSessionBuilder)

    def test_builder_is_not_an_iservice(self):
        from argus.lifecycle.interfaces import IService

        self.assertNotIsInstance(PlanningSessionBuilder(), IService)


class PlanningSessionBuilderEmptyTests(unittest.TestCase):
    def test_build_with_no_calls_returns_empty_session(self):
        session = PlanningSessionBuilder().build()
        self.assertIsInstance(session, PlanningSession)
        self.assertIsNone(session.cognitive_context)
        self.assertEqual(session.goals, ())
        self.assertEqual(session.constraints, ())
        self.assertEqual(session.tasks, ())
        self.assertEqual(dict(session.metadata.extra), {})


class PlanningSessionBuilderChainingTests(unittest.TestCase):
    def test_every_with_method_returns_the_builder(self):
        builder = PlanningSessionBuilder()
        self.assertIs(builder.with_context(CognitiveContext()), builder)
        self.assertIs(builder.with_goal(PlanningGoal(name="g1")), builder)
        self.assertIs(builder.with_constraint(PlanningConstraint(name="c1")), builder)
        self.assertIs(builder.with_metadata("key", "value"), builder)
        self.assertIs(builder.with_task(TaskBuilder().with_name("t1").build()), builder)
        self.assertIs(builder.with_tasks([TaskBuilder().with_name("t2").build()]), builder)
        self.assertIs(builder.clear_tasks(), builder)

    def test_full_fluent_chain_produces_populated_session(self):
        context = CognitiveContext(conversation_id="conv-1")
        goal = PlanningGoal(name="g1")
        constraint = PlanningConstraint(name="c1")
        task = TaskBuilder().with_name("t1").build()
        session = (
            PlanningSessionBuilder()
            .with_context(context)
            .with_goal(goal)
            .with_constraint(constraint)
            .with_task(task)
            .with_metadata("foo", "bar")
            .build()
        )
        self.assertIs(session.cognitive_context, context)
        self.assertEqual(session.goals, (goal,))
        self.assertEqual(session.constraints, (constraint,))
        self.assertEqual(session.tasks, (task,))
        self.assertEqual(dict(session.metadata.extra), {"foo": "bar"})

    def test_goals_accumulate_across_calls(self):
        g1, g2, g3 = PlanningGoal(name="g1"), PlanningGoal(name="g2"), PlanningGoal(name="g3")
        session = PlanningSessionBuilder().with_goal(g1).with_goal(g2).with_goal(g3).build()
        self.assertEqual(session.goals, (g1, g2, g3))

    def test_constraints_accumulate_across_calls(self):
        c1, c2 = PlanningConstraint(name="c1"), PlanningConstraint(name="c2")
        session = PlanningSessionBuilder().with_constraint(c1).with_constraint(c2).build()
        self.assertEqual(session.constraints, (c1, c2))

    def test_with_task_on_empty_builder_produces_single_task(self):
        task = TaskBuilder().with_name("t1").build()
        session = PlanningSessionBuilder().with_task(task).build()
        self.assertEqual(session.tasks, (task,))

    def test_tasks_accumulate_across_calls_preserving_insertion_order(self):
        t1 = TaskBuilder().with_name("t1").build()
        t2 = TaskBuilder().with_name("t2").build()
        t3 = TaskBuilder().with_name("t3").build()
        session = PlanningSessionBuilder().with_task(t1).with_task(t2).with_task(t3).build()
        self.assertEqual(session.tasks, (t1, t2, t3))

    def test_with_tasks_adds_multiple_in_order(self):
        t1 = TaskBuilder().with_name("t1").build()
        t2 = TaskBuilder().with_name("t2").build()
        session = PlanningSessionBuilder().with_tasks([t1, t2]).build()
        self.assertEqual(session.tasks, (t1, t2))

    def test_with_tasks_combines_with_prior_with_task_calls(self):
        t1 = TaskBuilder().with_name("t1").build()
        t2 = TaskBuilder().with_name("t2").build()
        t3 = TaskBuilder().with_name("t3").build()
        session = (
            PlanningSessionBuilder().with_task(t1).with_tasks([t2, t3]).build()
        )
        self.assertEqual(session.tasks, (t1, t2, t3))

    def test_clear_tasks_empties_previously_added_tasks(self):
        t1 = TaskBuilder().with_name("t1").build()
        session = PlanningSessionBuilder().with_task(t1).clear_tasks().build()
        self.assertEqual(session.tasks, ())

    def test_clear_tasks_then_re_add_produces_only_new_tasks(self):
        t1 = TaskBuilder().with_name("t1").build()
        t2 = TaskBuilder().with_name("t2").build()
        session = (
            PlanningSessionBuilder().with_task(t1).clear_tasks().with_task(t2).build()
        )
        self.assertEqual(session.tasks, (t2,))

    def test_with_task_rejects_duplicate_task_id_same_object(self):
        task = TaskBuilder().with_name("t1").build()
        builder = PlanningSessionBuilder().with_task(task)
        with self.assertRaises(InvalidPlanningSessionError):
            builder.with_task(task)

    def test_with_task_rejects_duplicate_task_id_different_object(self):
        task = TaskBuilder().with_name("t1").build()
        duplicate = Task(task_id=task.task_id, name="different-name")
        builder = PlanningSessionBuilder().with_task(task)
        with self.assertRaises(InvalidPlanningSessionError):
            builder.with_task(duplicate)

    def test_with_tasks_rejects_duplicate_task_id_within_the_batch(self):
        task = TaskBuilder().with_name("t1").build()
        duplicate = Task(task_id=task.task_id, name="different-name")
        with self.assertRaises(InvalidPlanningSessionError):
            PlanningSessionBuilder().with_tasks([task, duplicate])

    def test_with_tasks_rejects_duplicate_task_id_against_prior_with_task_call(self):
        task = TaskBuilder().with_name("t1").build()
        duplicate = Task(task_id=task.task_id, name="different-name")
        builder = PlanningSessionBuilder().with_task(task)
        with self.assertRaises(InvalidPlanningSessionError):
            builder.with_tasks([duplicate])

    def test_with_task_rejects_non_task(self):
        with self.assertRaises(InvalidPlanningSessionError):
            PlanningSessionBuilder().with_task("not a task")

    def test_with_task_rejects_none(self):
        with self.assertRaises(InvalidPlanningSessionError):
            PlanningSessionBuilder().with_task(None)

    def test_with_tasks_rejects_non_list_or_tuple(self):
        with self.assertRaises(InvalidPlanningSessionError):
            PlanningSessionBuilder().with_tasks("not a list")

    def test_with_tasks_accepts_tuple(self):
        t1 = TaskBuilder().with_name("t1").build()
        t2 = TaskBuilder().with_name("t2").build()
        session = PlanningSessionBuilder().with_tasks((t1, t2)).build()
        self.assertEqual(session.tasks, (t1, t2))

    def test_context_last_call_wins(self):
        first = CognitiveContext(conversation_id="first")
        second = CognitiveContext(conversation_id="second")
        session = PlanningSessionBuilder().with_context(first).with_context(second).build()
        self.assertIs(session.cognitive_context, second)

    def test_metadata_accumulates_distinct_keys(self):
        session = PlanningSessionBuilder().with_metadata("a", 1).with_metadata("b", 2).build()
        self.assertEqual(dict(session.metadata.extra), {"a": 1, "b": 2})

    def test_metadata_same_key_last_call_wins(self):
        session = PlanningSessionBuilder().with_metadata("k", 1).with_metadata("k", 2).build()
        self.assertEqual(dict(session.metadata.extra), {"k": 2})

    def test_metadata_value_may_be_none(self):
        session = PlanningSessionBuilder().with_metadata("k", None).build()
        self.assertEqual(dict(session.metadata.extra), {"k": None})


class PlanningSessionBuilderValidationTests(unittest.TestCase):
    def test_with_context_rejects_non_cognitive_context(self):
        with self.assertRaises(InvalidPlanningSessionError):
            PlanningSessionBuilder().with_context("not a context")

    def test_with_context_rejects_none(self):
        with self.assertRaises(InvalidPlanningSessionError):
            PlanningSessionBuilder().with_context(None)

    def test_with_goal_rejects_non_planning_goal(self):
        with self.assertRaises(InvalidPlanningSessionError):
            PlanningSessionBuilder().with_goal("not a goal")

    def test_with_goal_rejects_none(self):
        with self.assertRaises(InvalidPlanningSessionError):
            PlanningSessionBuilder().with_goal(None)

    def test_with_constraint_rejects_non_planning_constraint(self):
        with self.assertRaises(InvalidPlanningSessionError):
            PlanningSessionBuilder().with_constraint("not a constraint")

    def test_with_constraint_rejects_none(self):
        with self.assertRaises(InvalidPlanningSessionError):
            PlanningSessionBuilder().with_constraint(None)

    def test_with_metadata_rejects_empty_key(self):
        with self.assertRaises(InvalidPlanningSessionError):
            PlanningSessionBuilder().with_metadata("", "value")

    def test_with_metadata_rejects_none_key(self):
        with self.assertRaises(InvalidPlanningSessionError):
            PlanningSessionBuilder().with_metadata(None, "value")

    def test_with_metadata_rejects_non_string_key(self):
        with self.assertRaises(InvalidPlanningSessionError):
            PlanningSessionBuilder().with_metadata(5, "value")

    def test_validation_failure_does_not_partially_accumulate(self):
        builder = PlanningSessionBuilder().with_goal(PlanningGoal(name="g1"))
        with self.assertRaises(InvalidPlanningSessionError):
            builder.with_goal("not a goal")
        session = builder.build()
        self.assertEqual(len(session.goals), 1)


class PlanningSessionBuilderIndependenceTests(unittest.TestCase):
    def test_build_called_twice_returns_independent_sessions(self):
        builder = PlanningSessionBuilder().with_goal(PlanningGoal(name="g1"))
        first = builder.build()
        builder.with_goal(PlanningGoal(name="g2"))
        second = builder.build()
        self.assertEqual(len(first.goals), 1)
        self.assertEqual(len(second.goals), 2)
        self.assertNotEqual(first.session_id, second.session_id)

    def test_mutating_returned_session_sequence_does_not_affect_builder_state(self):
        builder = PlanningSessionBuilder().with_goal(PlanningGoal(name="g1"))
        session = builder.build()
        with self.assertRaises(AttributeError):
            session.goals.append(PlanningGoal(name="g2"))

    def test_each_build_gets_a_fresh_metadata_instance(self):
        builder = PlanningSessionBuilder()
        first = builder.build()
        second = builder.build()
        self.assertNotEqual(first.metadata.correlation_id, second.metadata.correlation_id)


if __name__ == "__main__":
    unittest.main()
