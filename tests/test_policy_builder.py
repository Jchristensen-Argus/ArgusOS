"""Unit tests for argus.policy.builder.PolicyBuilder."""

import unittest

from argus.policy import (
    IPolicyBuilder,
    InvalidPolicyError,
    PolicyBuilder,
    PolicyScope,
    PolicyStatus,
)


class IdentityTests(unittest.TestCase):
    def test_is_an_ipolicybuilder(self):
        self.assertIsInstance(PolicyBuilder(), IPolicyBuilder)

    def test_is_not_an_iservice(self):
        from argus.lifecycle import IService

        self.assertNotIsInstance(PolicyBuilder(), IService)

    def test_starts_with_default_values(self):
        policy = PolicyBuilder().build()
        self.assertEqual(policy.name, "")
        self.assertEqual(policy.description, "")
        self.assertEqual(policy.status, PolicyStatus.ACTIVE)
        self.assertEqual(policy.scope, PolicyScope.GLOBAL)

    def test_constructor_takes_no_arguments(self):
        builder = PolicyBuilder()
        self.assertIsInstance(builder, PolicyBuilder)

    def test_no_with_policy_id_method_exists(self):
        self.assertFalse(hasattr(PolicyBuilder(), "with_policy_id"))

    def test_no_with_owner_method_exists(self):
        self.assertFalse(hasattr(PolicyBuilder(), "with_owner"))

    def test_no_with_tags_method_exists(self):
        self.assertFalse(hasattr(PolicyBuilder(), "with_tags"))

    def test_has_with_scope_method(self):
        # Unlike owner/tags, scope is explicitly named in this
        # package's own Responsibilities list - see builder.py's own
        # module docstring.
        self.assertTrue(hasattr(PolicyBuilder(), "with_scope"))


class WithNameTests(unittest.TestCase):
    def test_with_name_returns_self_for_chaining(self):
        builder = PolicyBuilder()
        result = builder.with_name("Max spend limit")
        self.assertIs(result, builder)

    def test_with_name_is_overwritten_not_accumulated(self):
        policy = PolicyBuilder().with_name("First").with_name("Second").build()
        self.assertEqual(policy.name, "Second")

    def test_with_name_rejects_empty_string(self):
        with self.assertRaises(InvalidPolicyError):
            PolicyBuilder().with_name("")

    def test_with_name_rejects_non_string(self):
        with self.assertRaises(InvalidPolicyError):
            PolicyBuilder().with_name(123)

    def test_with_name_rejects_none(self):
        with self.assertRaises(InvalidPolicyError):
            PolicyBuilder().with_name(None)


class WithDescriptionTests(unittest.TestCase):
    def test_with_description_returns_self_for_chaining(self):
        builder = PolicyBuilder()
        result = builder.with_description("Cap total automated spend")
        self.assertIs(result, builder)

    def test_with_description_is_overwritten_not_accumulated(self):
        policy = (
            PolicyBuilder()
            .with_description("First")
            .with_description("Second")
            .build()
        )
        self.assertEqual(policy.description, "Second")

    def test_with_description_accepts_empty_string(self):
        policy = PolicyBuilder().with_description("").build()
        self.assertEqual(policy.description, "")

    def test_with_description_rejects_non_string(self):
        with self.assertRaises(InvalidPolicyError):
            PolicyBuilder().with_description(123)

    def test_with_description_rejects_none(self):
        with self.assertRaises(InvalidPolicyError):
            PolicyBuilder().with_description(None)


class WithStatusTests(unittest.TestCase):
    def test_with_status_returns_self_for_chaining(self):
        builder = PolicyBuilder()
        result = builder.with_status(PolicyStatus.INACTIVE)
        self.assertIs(result, builder)

    def test_with_status_is_overwritten_not_accumulated(self):
        policy = (
            PolicyBuilder()
            .with_status(PolicyStatus.INACTIVE)
            .with_status(PolicyStatus.ARCHIVED)
            .build()
        )
        self.assertEqual(policy.status, PolicyStatus.ARCHIVED)

    def test_with_status_rejects_non_status(self):
        with self.assertRaises(InvalidPolicyError):
            PolicyBuilder().with_status("active")

    def test_with_status_rejects_none(self):
        with self.assertRaises(InvalidPolicyError):
            PolicyBuilder().with_status(None)

    def test_default_status_is_active(self):
        policy = PolicyBuilder().build()
        self.assertEqual(policy.status, PolicyStatus.ACTIVE)


class WithScopeTests(unittest.TestCase):
    def test_with_scope_returns_self_for_chaining(self):
        builder = PolicyBuilder()
        result = builder.with_scope(PolicyScope.PROJECT)
        self.assertIs(result, builder)

    def test_with_scope_is_overwritten_not_accumulated(self):
        policy = (
            PolicyBuilder()
            .with_scope(PolicyScope.PROJECT)
            .with_scope(PolicyScope.TASK)
            .build()
        )
        self.assertEqual(policy.scope, PolicyScope.TASK)

    def test_with_scope_rejects_non_scope(self):
        with self.assertRaises(InvalidPolicyError):
            PolicyBuilder().with_scope("global")

    def test_with_scope_rejects_none(self):
        with self.assertRaises(InvalidPolicyError):
            PolicyBuilder().with_scope(None)

    def test_default_scope_is_global(self):
        policy = PolicyBuilder().build()
        self.assertEqual(policy.scope, PolicyScope.GLOBAL)


class WithMetadataTests(unittest.TestCase):
    def test_with_metadata_returns_self_for_chaining(self):
        builder = PolicyBuilder()
        result = builder.with_metadata("k", "v")
        self.assertIs(result, builder)

    def test_with_metadata_populates_extra(self):
        policy = PolicyBuilder().with_metadata("severity", "high").build()
        self.assertEqual(policy.metadata.extra["severity"], "high")

    def test_with_metadata_accumulates_distinct_keys(self):
        policy = PolicyBuilder().with_metadata("a", 1).with_metadata("b", 2).build()
        self.assertEqual(dict(policy.metadata.extra), {"a": 1, "b": 2})

    def test_with_metadata_same_key_overwrites(self):
        policy = (
            PolicyBuilder()
            .with_metadata("k", "first")
            .with_metadata("k", "second")
            .build()
        )
        self.assertEqual(policy.metadata.extra["k"], "second")

    def test_with_metadata_rejects_empty_key(self):
        with self.assertRaises(InvalidPolicyError):
            PolicyBuilder().with_metadata("", "v")

    def test_with_metadata_rejects_non_string_key(self):
        with self.assertRaises(InvalidPolicyError):
            PolicyBuilder().with_metadata(123, "v")

    def test_with_metadata_cannot_set_owner_or_tags(self):
        policy = PolicyBuilder().with_metadata("owner", "Jane").build()
        self.assertIsNone(policy.metadata.owner)
        self.assertEqual(policy.metadata.extra["owner"], "Jane")


class BuildTests(unittest.TestCase):
    def test_build_with_no_calls_produces_a_default_policy(self):
        policy = PolicyBuilder().build()
        self.assertEqual(policy.name, "")
        self.assertEqual(policy.description, "")
        self.assertEqual(policy.status, PolicyStatus.ACTIVE)
        self.assertEqual(policy.scope, PolicyScope.GLOBAL)

    def test_build_produces_a_fresh_policy_id_each_call(self):
        builder = PolicyBuilder().with_name("Max spend limit")
        first = builder.build()
        second = builder.build()
        self.assertNotEqual(first.policy_id, second.policy_id)

    def test_build_after_build_does_not_mutate_the_earlier_policy(self):
        builder = PolicyBuilder().with_name("First")
        first = builder.build()
        builder.with_name("Second")
        second = builder.build()
        self.assertEqual(first.name, "First")
        self.assertEqual(second.name, "Second")

    def test_full_chain_produces_the_expected_policy(self):
        policy = (
            PolicyBuilder()
            .with_name("Human approval required")
            .with_description("Require sign-off before high-risk execution")
            .with_status(PolicyStatus.ACTIVE)
            .with_scope(PolicyScope.CAPABILITY)
            .with_metadata("k", "v")
            .build()
        )
        self.assertEqual(policy.name, "Human approval required")
        self.assertEqual(
            policy.description, "Require sign-off before high-risk execution"
        )
        self.assertEqual(policy.status, PolicyStatus.ACTIVE)
        self.assertEqual(policy.scope, PolicyScope.CAPABILITY)
        self.assertEqual(policy.metadata.extra["k"], "v")


if __name__ == "__main__":
    unittest.main()
