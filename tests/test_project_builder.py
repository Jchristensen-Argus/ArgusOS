"""Unit tests for argus.project.builder.ProjectBuilder."""

import unittest

from argus.project import (
    IProjectBuilder,
    InvalidProjectError,
    ProjectBuilder,
    ProjectStatus,
)


class IdentityTests(unittest.TestCase):
    def test_is_an_iprojectbuilder(self):
        self.assertIsInstance(ProjectBuilder(), IProjectBuilder)

    def test_is_not_an_iservice(self):
        from argus.lifecycle import IService

        self.assertNotIsInstance(ProjectBuilder(), IService)

    def test_starts_with_default_values(self):
        project = ProjectBuilder().build()
        self.assertEqual(project.name, "")
        self.assertEqual(project.description, "")
        self.assertEqual(project.status, ProjectStatus.PLANNING)

    def test_constructor_takes_no_arguments(self):
        builder = ProjectBuilder()
        self.assertIsInstance(builder, ProjectBuilder)

    def test_no_with_project_id_method_exists(self):
        # This package's own Responsibilities list does not name
        # "assign id" - matching RelationshipBuilder's (031),
        # ExecutionResultBuilder's (032), CapabilityExecutionResultBuilder's
        # (034), and CapabilityContextBuilder's (035) own shape. See
        # builder.py's own module docstring.
        self.assertFalse(hasattr(ProjectBuilder(), "with_project_id"))

    def test_no_with_owner_method_exists(self):
        # owner is system-managed, not builder-overridable in Version
        # 1 - see metadata.py's own module docstring.
        self.assertFalse(hasattr(ProjectBuilder(), "with_owner"))

    def test_no_with_tags_method_exists(self):
        # tags is system-managed, not builder-overridable in Version
        # 1 - see metadata.py's own module docstring.
        self.assertFalse(hasattr(ProjectBuilder(), "with_tags"))


class WithNameTests(unittest.TestCase):
    def test_with_name_returns_self_for_chaining(self):
        builder = ProjectBuilder()
        result = builder.with_name("ArgusOS")
        self.assertIs(result, builder)

    def test_with_name_is_overwritten_not_accumulated(self):
        project = ProjectBuilder().with_name("First").with_name("Second").build()
        self.assertEqual(project.name, "Second")

    def test_with_name_rejects_empty_string(self):
        with self.assertRaises(InvalidProjectError):
            ProjectBuilder().with_name("")

    def test_with_name_rejects_non_string(self):
        with self.assertRaises(InvalidProjectError):
            ProjectBuilder().with_name(123)

    def test_with_name_rejects_none(self):
        with self.assertRaises(InvalidProjectError):
            ProjectBuilder().with_name(None)


class WithDescriptionTests(unittest.TestCase):
    def test_with_description_returns_self_for_chaining(self):
        builder = ProjectBuilder()
        result = builder.with_description("A soap business")
        self.assertIs(result, builder)

    def test_with_description_is_overwritten_not_accumulated(self):
        project = (
            ProjectBuilder().with_description("First").with_description("Second").build()
        )
        self.assertEqual(project.description, "Second")

    def test_with_description_accepts_empty_string(self):
        project = ProjectBuilder().with_description("").build()
        self.assertEqual(project.description, "")

    def test_with_description_rejects_non_string(self):
        with self.assertRaises(InvalidProjectError):
            ProjectBuilder().with_description(123)

    def test_with_description_rejects_none(self):
        with self.assertRaises(InvalidProjectError):
            ProjectBuilder().with_description(None)


class WithStatusTests(unittest.TestCase):
    def test_with_status_returns_self_for_chaining(self):
        builder = ProjectBuilder()
        result = builder.with_status(ProjectStatus.ACTIVE)
        self.assertIs(result, builder)

    def test_with_status_is_overwritten_not_accumulated(self):
        project = (
            ProjectBuilder()
            .with_status(ProjectStatus.ACTIVE)
            .with_status(ProjectStatus.PAUSED)
            .build()
        )
        self.assertEqual(project.status, ProjectStatus.PAUSED)

    def test_with_status_rejects_non_status(self):
        with self.assertRaises(InvalidProjectError):
            ProjectBuilder().with_status("active")

    def test_with_status_rejects_none(self):
        with self.assertRaises(InvalidProjectError):
            ProjectBuilder().with_status(None)

    def test_default_status_is_planning(self):
        project = ProjectBuilder().build()
        self.assertEqual(project.status, ProjectStatus.PLANNING)


class WithMetadataTests(unittest.TestCase):
    def test_with_metadata_returns_self_for_chaining(self):
        builder = ProjectBuilder()
        result = builder.with_metadata("k", "v")
        self.assertIs(result, builder)

    def test_with_metadata_populates_extra(self):
        project = ProjectBuilder().with_metadata("region", "US").build()
        self.assertEqual(project.metadata.extra["region"], "US")

    def test_with_metadata_accumulates_distinct_keys(self):
        project = (
            ProjectBuilder().with_metadata("a", 1).with_metadata("b", 2).build()
        )
        self.assertEqual(dict(project.metadata.extra), {"a": 1, "b": 2})

    def test_with_metadata_same_key_overwrites(self):
        project = (
            ProjectBuilder()
            .with_metadata("k", "first")
            .with_metadata("k", "second")
            .build()
        )
        self.assertEqual(project.metadata.extra["k"], "second")

    def test_with_metadata_rejects_empty_key(self):
        with self.assertRaises(InvalidProjectError):
            ProjectBuilder().with_metadata("", "v")

    def test_with_metadata_rejects_non_string_key(self):
        with self.assertRaises(InvalidProjectError):
            ProjectBuilder().with_metadata(123, "v")

    def test_with_metadata_cannot_set_owner_or_tags(self):
        # with_metadata() only ever populates extra - owner/tags
        # remain at their own defaults regardless.
        project = ProjectBuilder().with_metadata("owner", "Jane").build()
        self.assertIsNone(project.metadata.owner)
        self.assertEqual(project.metadata.extra["owner"], "Jane")


class BuildTests(unittest.TestCase):
    def test_build_with_no_calls_produces_a_default_project(self):
        project = ProjectBuilder().build()
        self.assertEqual(project.name, "")
        self.assertEqual(project.description, "")
        self.assertEqual(project.status, ProjectStatus.PLANNING)

    def test_build_produces_a_fresh_project_id_each_call(self):
        builder = ProjectBuilder().with_name("ArgusOS")
        first = builder.build()
        second = builder.build()
        self.assertNotEqual(first.project_id, second.project_id)

    def test_build_after_build_does_not_mutate_the_earlier_project(self):
        builder = ProjectBuilder().with_name("First")
        first = builder.build()
        builder.with_name("Second")
        second = builder.build()
        self.assertEqual(first.name, "First")
        self.assertEqual(second.name, "Second")

    def test_full_chain_produces_the_expected_project(self):
        project = (
            ProjectBuilder()
            .with_name("Just Tallow")
            .with_description("Soap business")
            .with_status(ProjectStatus.ACTIVE)
            .with_metadata("k", "v")
            .build()
        )
        self.assertEqual(project.name, "Just Tallow")
        self.assertEqual(project.description, "Soap business")
        self.assertEqual(project.status, ProjectStatus.ACTIVE)
        self.assertEqual(project.metadata.extra["k"], "v")


if __name__ == "__main__":
    unittest.main()
