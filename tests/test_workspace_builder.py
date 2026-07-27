"""Unit tests for argus.workspace.builder.WorkspaceBuilder."""

import unittest

from argus.workspace import (
    IWorkspaceBuilder,
    InvalidWorkspaceError,
    WorkspaceBuilder,
    WorkspaceStatus,
)


class IdentityTests(unittest.TestCase):
    def test_is_an_iworkspacebuilder(self):
        self.assertIsInstance(WorkspaceBuilder(), IWorkspaceBuilder)

    def test_is_not_an_iservice(self):
        from argus.lifecycle import IService

        self.assertNotIsInstance(WorkspaceBuilder(), IService)

    def test_starts_with_default_values(self):
        workspace = WorkspaceBuilder().build()
        self.assertEqual(workspace.name, "")
        self.assertEqual(workspace.description, "")
        self.assertEqual(workspace.status, WorkspaceStatus.ACTIVE)

    def test_constructor_takes_no_arguments(self):
        builder = WorkspaceBuilder()
        self.assertIsInstance(builder, WorkspaceBuilder)

    def test_no_with_workspace_id_method_exists(self):
        # This package's own Responsibilities list does not name
        # "assign id" - matching RelationshipBuilder's (031),
        # ExecutionResultBuilder's (032),
        # CapabilityExecutionResultBuilder's (034),
        # CapabilityContextBuilder's (035), and ProjectBuilder's (036)
        # own shape. See builder.py's own module docstring.
        self.assertFalse(hasattr(WorkspaceBuilder(), "with_workspace_id"))

    def test_no_with_owner_method_exists(self):
        # owner is system-managed, not builder-overridable in Version
        # 1 - see metadata.py's own module docstring.
        self.assertFalse(hasattr(WorkspaceBuilder(), "with_owner"))

    def test_no_with_tags_method_exists(self):
        # tags is system-managed, not builder-overridable in Version
        # 1 - see metadata.py's own module docstring.
        self.assertFalse(hasattr(WorkspaceBuilder(), "with_tags"))


class WithNameTests(unittest.TestCase):
    def test_with_name_returns_self_for_chaining(self):
        builder = WorkspaceBuilder()
        result = builder.with_name("ArgusOS")
        self.assertIs(result, builder)

    def test_with_name_is_overwritten_not_accumulated(self):
        workspace = WorkspaceBuilder().with_name("First").with_name("Second").build()
        self.assertEqual(workspace.name, "Second")

    def test_with_name_rejects_empty_string(self):
        with self.assertRaises(InvalidWorkspaceError):
            WorkspaceBuilder().with_name("")

    def test_with_name_rejects_non_string(self):
        with self.assertRaises(InvalidWorkspaceError):
            WorkspaceBuilder().with_name(123)

    def test_with_name_rejects_none(self):
        with self.assertRaises(InvalidWorkspaceError):
            WorkspaceBuilder().with_name(None)


class WithDescriptionTests(unittest.TestCase):
    def test_with_description_returns_self_for_chaining(self):
        builder = WorkspaceBuilder()
        result = builder.with_description("A personal workspace")
        self.assertIs(result, builder)

    def test_with_description_is_overwritten_not_accumulated(self):
        workspace = (
            WorkspaceBuilder()
            .with_description("First")
            .with_description("Second")
            .build()
        )
        self.assertEqual(workspace.description, "Second")

    def test_with_description_accepts_empty_string(self):
        workspace = WorkspaceBuilder().with_description("").build()
        self.assertEqual(workspace.description, "")

    def test_with_description_rejects_non_string(self):
        with self.assertRaises(InvalidWorkspaceError):
            WorkspaceBuilder().with_description(123)

    def test_with_description_rejects_none(self):
        with self.assertRaises(InvalidWorkspaceError):
            WorkspaceBuilder().with_description(None)


class WithStatusTests(unittest.TestCase):
    def test_with_status_returns_self_for_chaining(self):
        builder = WorkspaceBuilder()
        result = builder.with_status(WorkspaceStatus.INACTIVE)
        self.assertIs(result, builder)

    def test_with_status_is_overwritten_not_accumulated(self):
        workspace = (
            WorkspaceBuilder()
            .with_status(WorkspaceStatus.INACTIVE)
            .with_status(WorkspaceStatus.ARCHIVED)
            .build()
        )
        self.assertEqual(workspace.status, WorkspaceStatus.ARCHIVED)

    def test_with_status_rejects_non_status(self):
        with self.assertRaises(InvalidWorkspaceError):
            WorkspaceBuilder().with_status("active")

    def test_with_status_rejects_none(self):
        with self.assertRaises(InvalidWorkspaceError):
            WorkspaceBuilder().with_status(None)

    def test_default_status_is_active(self):
        workspace = WorkspaceBuilder().build()
        self.assertEqual(workspace.status, WorkspaceStatus.ACTIVE)


class WithMetadataTests(unittest.TestCase):
    def test_with_metadata_returns_self_for_chaining(self):
        builder = WorkspaceBuilder()
        result = builder.with_metadata("k", "v")
        self.assertIs(result, builder)

    def test_with_metadata_populates_extra(self):
        workspace = WorkspaceBuilder().with_metadata("region", "US").build()
        self.assertEqual(workspace.metadata.extra["region"], "US")

    def test_with_metadata_accumulates_distinct_keys(self):
        workspace = (
            WorkspaceBuilder().with_metadata("a", 1).with_metadata("b", 2).build()
        )
        self.assertEqual(dict(workspace.metadata.extra), {"a": 1, "b": 2})

    def test_with_metadata_same_key_overwrites(self):
        workspace = (
            WorkspaceBuilder()
            .with_metadata("k", "first")
            .with_metadata("k", "second")
            .build()
        )
        self.assertEqual(workspace.metadata.extra["k"], "second")

    def test_with_metadata_rejects_empty_key(self):
        with self.assertRaises(InvalidWorkspaceError):
            WorkspaceBuilder().with_metadata("", "v")

    def test_with_metadata_rejects_non_string_key(self):
        with self.assertRaises(InvalidWorkspaceError):
            WorkspaceBuilder().with_metadata(123, "v")

    def test_with_metadata_cannot_set_owner_or_tags(self):
        # with_metadata() only ever populates extra - owner/tags
        # remain at their own defaults regardless.
        workspace = WorkspaceBuilder().with_metadata("owner", "Jane").build()
        self.assertIsNone(workspace.metadata.owner)
        self.assertEqual(workspace.metadata.extra["owner"], "Jane")


class BuildTests(unittest.TestCase):
    def test_build_with_no_calls_produces_a_default_workspace(self):
        workspace = WorkspaceBuilder().build()
        self.assertEqual(workspace.name, "")
        self.assertEqual(workspace.description, "")
        self.assertEqual(workspace.status, WorkspaceStatus.ACTIVE)

    def test_build_produces_a_fresh_workspace_id_each_call(self):
        builder = WorkspaceBuilder().with_name("ArgusOS")
        first = builder.build()
        second = builder.build()
        self.assertNotEqual(first.workspace_id, second.workspace_id)

    def test_build_after_build_does_not_mutate_the_earlier_workspace(self):
        builder = WorkspaceBuilder().with_name("First")
        first = builder.build()
        builder.with_name("Second")
        second = builder.build()
        self.assertEqual(first.name, "First")
        self.assertEqual(second.name, "Second")

    def test_full_chain_produces_the_expected_workspace(self):
        workspace = (
            WorkspaceBuilder()
            .with_name("Joel Christensen")
            .with_description("Personal workspace")
            .with_status(WorkspaceStatus.INACTIVE)
            .with_metadata("k", "v")
            .build()
        )
        self.assertEqual(workspace.name, "Joel Christensen")
        self.assertEqual(workspace.description, "Personal workspace")
        self.assertEqual(workspace.status, WorkspaceStatus.INACTIVE)
        self.assertEqual(workspace.metadata.extra["k"], "v")


if __name__ == "__main__":
    unittest.main()
