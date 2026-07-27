"""Unit tests for argus.policy.policy.Policy."""

import copy
import dataclasses
import pickle
import unittest

from argus.policy import Policy, PolicyMetadata, PolicyScope, PolicyStatus


class DefaultsTests(unittest.TestCase):
    def test_defaults(self):
        policy = Policy()
        self.assertTrue(policy.policy_id)
        self.assertEqual(policy.name, "")
        self.assertEqual(policy.description, "")
        self.assertEqual(policy.status, PolicyStatus.ACTIVE)
        self.assertEqual(policy.scope, PolicyScope.GLOBAL)
        self.assertIsInstance(policy.metadata, PolicyMetadata)

    def test_all_fields_set(self):
        metadata = PolicyMetadata(extra={"k": "v"})
        policy = Policy(
            policy_id="fixed-id",
            name="Human approval required",
            description="Require sign-off before high-risk execution",
            status=PolicyStatus.INACTIVE,
            scope=PolicyScope.CAPABILITY,
            metadata=metadata,
        )
        self.assertEqual(policy.policy_id, "fixed-id")
        self.assertEqual(policy.name, "Human approval required")
        self.assertEqual(
            policy.description, "Require sign-off before high-risk execution"
        )
        self.assertEqual(policy.status, PolicyStatus.INACTIVE)
        self.assertEqual(policy.scope, PolicyScope.CAPABILITY)
        self.assertIs(policy.metadata, metadata)

    def test_default_policy_id_is_unique_per_instance(self):
        a = Policy()
        b = Policy()
        self.assertNotEqual(a.policy_id, b.policy_id)


class FieldOrderTests(unittest.TestCase):
    def test_field_order_places_metadata_last(self):
        field_names = [f.name for f in dataclasses.fields(Policy)]
        self.assertEqual(
            field_names,
            ["policy_id", "name", "description", "status", "scope", "metadata"],
        )


class DefaultStatusAndScopeTests(unittest.TestCase):
    def test_default_status_is_active(self):
        # Matches WorkspaceStatus's own default (037), since neither
        # member list names a "not yet begun" state - see status.py's
        # own module docstring.
        self.assertEqual(Policy().status, PolicyStatus.ACTIVE)

    def test_default_scope_is_global(self):
        self.assertEqual(Policy().scope, PolicyScope.GLOBAL)


class ImmutabilityTests(unittest.TestCase):
    def test_immutability(self):
        policy = Policy()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            policy.policy_id = "mutated"

    def test_name_field_immutable(self):
        policy = Policy()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            policy.name = "mutated"

    def test_scope_field_immutable(self):
        policy = Policy()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            policy.scope = PolicyScope.TASK

    def test_metadata_field_immutable(self):
        policy = Policy()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            policy.metadata = PolicyMetadata()


class MiscellaneousRobustnessTests(unittest.TestCase):
    def test_deepcopy_of_scalar_fields_round_trips_equal(self):
        policy = Policy()
        copied_id = copy.deepcopy(policy.policy_id)
        self.assertEqual(copied_id, policy.policy_id)

    def test_pickle_of_scalar_fields_round_trips_equal(self):
        policy = Policy()
        self.assertEqual(pickle.loads(pickle.dumps(policy.policy_id)), policy.policy_id)
        self.assertIs(pickle.loads(pickle.dumps(policy.status)), policy.status)
        self.assertIs(pickle.loads(pickle.dumps(policy.scope)), policy.scope)

    def test_policy_id_is_a_plain_string_suitable_for_json(self):
        policy = Policy()
        self.assertIsInstance(policy.policy_id, str)


class EqualityTests(unittest.TestCase):
    def test_equality_when_all_fields_match(self):
        metadata = PolicyMetadata()
        a = Policy(policy_id="p1", name="Max spend limit", metadata=metadata)
        b = Policy(policy_id="p1", name="Max spend limit", metadata=metadata)
        self.assertEqual(a, b)

    def test_not_equal_when_policy_id_differs(self):
        metadata = PolicyMetadata()
        a = Policy(policy_id="p1", metadata=metadata)
        b = Policy(policy_id="p2", metadata=metadata)
        self.assertNotEqual(a, b)

    def test_not_equal_when_scope_differs(self):
        metadata = PolicyMetadata()
        a = Policy(policy_id="p1", scope=PolicyScope.GLOBAL, metadata=metadata)
        b = Policy(policy_id="p1", scope=PolicyScope.TASK, metadata=metadata)
        self.assertNotEqual(a, b)

    def test_not_equal_when_status_differs(self):
        metadata = PolicyMetadata()
        a = Policy(policy_id="p1", status=PolicyStatus.ACTIVE, metadata=metadata)
        b = Policy(policy_id="p1", status=PolicyStatus.ARCHIVED, metadata=metadata)
        self.assertNotEqual(a, b)


if __name__ == "__main__":
    unittest.main()
