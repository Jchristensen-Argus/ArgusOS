"""Unit tests for argus.task.status.TaskStatus."""

import unittest
from enum import Enum

from argus.task import TaskStatus


class EnumerationCorrectnessTests(unittest.TestCase):
    def test_is_a_plain_enum_not_a_str_subclass(self):
        # Mirrors PlanStatus's own shape - a plain Enum, not a str
        # subclass.
        self.assertTrue(issubclass(TaskStatus, Enum))
        self.assertFalse(issubclass(TaskStatus, str))

    def test_exactly_five_members(self):
        self.assertEqual(len(TaskStatus), 5)

    def test_member_names(self):
        self.assertEqual(
            {member.name for member in TaskStatus},
            {"PENDING", "READY", "COMPLETED", "FAILED", "CANCELLED"},
        )

    def test_member_values(self):
        self.assertEqual(TaskStatus.PENDING.value, "pending")
        self.assertEqual(TaskStatus.READY.value, "ready")
        self.assertEqual(TaskStatus.COMPLETED.value, "completed")
        self.assertEqual(TaskStatus.FAILED.value, "failed")
        self.assertEqual(TaskStatus.CANCELLED.value, "cancelled")

    def test_values_are_all_distinct(self):
        values = [member.value for member in TaskStatus]
        self.assertEqual(len(values), len(set(values)))


class NoTransitionsTests(unittest.TestCase):
    def test_status_has_no_transition_methods(self):
        # "Do not implement transitions" - TaskStatus is a bare
        # enumeration with no methods of its own beyond what Enum
        # itself provides.
        own_attrs = set(vars(TaskStatus)) - set(vars(Enum))
        member_names = {member.name for member in TaskStatus}
        # Everything TaskStatus defines beyond inherited Enum
        # machinery is either a member or dunder/sunder plumbing -
        # no callable "next_status"/"transition_to"/etc. exists.
        suspicious = {
            name
            for name in own_attrs
            if not name.startswith("_") and name not in member_names
        }
        self.assertEqual(suspicious, set())


class EqualityAndIdentityTests(unittest.TestCase):
    def test_members_are_singletons(self):
        self.assertIs(TaskStatus.PENDING, TaskStatus("pending"))

    def test_different_members_are_not_equal(self):
        self.assertNotEqual(TaskStatus.PENDING, TaskStatus.READY)


if __name__ == "__main__":
    unittest.main()
