"""Unit tests for argus.scheduler.task.ScheduledTask and TaskPriority."""

import dataclasses
import unittest
import uuid
from datetime import datetime, timezone

from argus.scheduler import OneShotTrigger, ScheduledTask, TaskPriority


def _trigger():
    return OneShotTrigger(run_at=datetime(2026, 1, 1, tzinfo=timezone.utc))


class ScheduledTaskTests(unittest.TestCase):
    def test_stores_name_callback_and_trigger(self):
        callback = lambda: None
        trigger = _trigger()

        task = ScheduledTask(name="a", callback=callback, trigger=trigger)

        self.assertEqual(task.name, "a")
        self.assertIs(task.callback, callback)
        self.assertIs(task.trigger, trigger)

    def test_id_is_auto_generated_and_is_a_valid_uuid(self):
        task = ScheduledTask(name="a", callback=lambda: None, trigger=_trigger())

        self.assertTrue(task.id)
        uuid.UUID(task.id)

    def test_two_tasks_get_different_ids(self):
        first = ScheduledTask(name="a", callback=lambda: None, trigger=_trigger())
        second = ScheduledTask(name="b", callback=lambda: None, trigger=_trigger())

        self.assertNotEqual(first.id, second.id)

    def test_priority_defaults_to_normal(self):
        task = ScheduledTask(name="a", callback=lambda: None, trigger=_trigger())

        self.assertEqual(task.priority, TaskPriority.NORMAL)

    def test_enabled_defaults_to_true(self):
        task = ScheduledTask(name="a", callback=lambda: None, trigger=_trigger())

        self.assertTrue(task.enabled)

    def test_created_at_is_auto_generated(self):
        task = ScheduledTask(name="a", callback=lambda: None, trigger=_trigger())

        self.assertIsInstance(task.created_at, datetime)

    def test_next_run_and_last_run_default_to_none(self):
        task = ScheduledTask(name="a", callback=lambda: None, trigger=_trigger())

        self.assertIsNone(task.next_run)
        self.assertIsNone(task.last_run)

    def test_task_is_immutable(self):
        task = ScheduledTask(name="a", callback=lambda: None, trigger=_trigger())

        with self.assertRaises(dataclasses.FrozenInstanceError):
            task.enabled = False

    def test_replace_produces_a_new_task_without_mutating_the_original(self):
        original = ScheduledTask(name="a", callback=lambda: None, trigger=_trigger())

        updated = dataclasses.replace(original, enabled=False)

        self.assertTrue(original.enabled)
        self.assertFalse(updated.enabled)
        self.assertEqual(updated.id, original.id)


class TaskPriorityTests(unittest.TestCase):
    def test_expected_members_exist(self):
        self.assertEqual(
            {member.name for member in TaskPriority}, {"LOW", "NORMAL", "HIGH", "CRITICAL"}
        )


if __name__ == "__main__":
    unittest.main()
