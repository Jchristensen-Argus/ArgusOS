"""Unit tests for argus.project.project.Project."""

import copy
import dataclasses
import pickle
import unittest

from argus.project import Project, ProjectMetadata, ProjectStatus


class DefaultsTests(unittest.TestCase):
    def test_defaults(self):
        project = Project()
        self.assertTrue(project.project_id)
        self.assertEqual(project.name, "")
        self.assertEqual(project.description, "")
        self.assertEqual(project.status, ProjectStatus.PLANNING)
        self.assertIsInstance(project.metadata, ProjectMetadata)

    def test_all_fields_set(self):
        metadata = ProjectMetadata(extra={"k": "v"})
        project = Project(
            project_id="fixed-id",
            name="Just Tallow",
            description="Soap business",
            status=ProjectStatus.ACTIVE,
            metadata=metadata,
        )
        self.assertEqual(project.project_id, "fixed-id")
        self.assertEqual(project.name, "Just Tallow")
        self.assertEqual(project.description, "Soap business")
        self.assertEqual(project.status, ProjectStatus.ACTIVE)
        self.assertIs(project.metadata, metadata)

    def test_default_project_id_is_unique_per_instance(self):
        a = Project()
        b = Project()
        self.assertNotEqual(a.project_id, b.project_id)


class FieldOrderTests(unittest.TestCase):
    def test_field_order_places_metadata_last(self):
        field_names = [f.name for f in dataclasses.fields(Project)]
        self.assertEqual(
            field_names, ["project_id", "name", "description", "status", "metadata"]
        )


class ExampleNamesTests(unittest.TestCase):
    def test_accepts_every_example_name_from_the_work_order(self):
        # "Examples: Just Tallow, Packaging Sales, ArgusOS, Book
        # Publishing, Real Estate, Marketing, Personal."
        for name in (
            "Just Tallow",
            "Packaging Sales",
            "ArgusOS",
            "Book Publishing",
            "Real Estate",
            "Marketing",
            "Personal",
        ):
            project = Project(name=name)
            self.assertEqual(project.name, name)


class ImmutabilityTests(unittest.TestCase):
    def test_immutability(self):
        project = Project()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            project.project_id = "mutated"

    def test_name_field_immutable(self):
        project = Project()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            project.name = "mutated"

    def test_metadata_field_immutable(self):
        project = Project()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            project.metadata = ProjectMetadata()


class MiscellaneousRobustnessTests(unittest.TestCase):
    def test_deepcopy_of_scalar_fields_round_trips_equal(self):
        project = Project()
        copied_id = copy.deepcopy(project.project_id)
        self.assertEqual(copied_id, project.project_id)

    def test_pickle_of_scalar_fields_round_trips_equal(self):
        project = Project()
        self.assertEqual(
            pickle.loads(pickle.dumps(project.project_id)), project.project_id
        )
        self.assertIs(pickle.loads(pickle.dumps(project.status)), project.status)

    def test_project_id_is_a_plain_string_suitable_for_json(self):
        project = Project()
        self.assertIsInstance(project.project_id, str)


class EqualityTests(unittest.TestCase):
    def test_equality_when_all_fields_match(self):
        metadata = ProjectMetadata()
        a = Project(project_id="p1", name="ArgusOS", metadata=metadata)
        b = Project(project_id="p1", name="ArgusOS", metadata=metadata)
        self.assertEqual(a, b)

    def test_not_equal_when_project_id_differs(self):
        metadata = ProjectMetadata()
        a = Project(project_id="p1", metadata=metadata)
        b = Project(project_id="p2", metadata=metadata)
        self.assertNotEqual(a, b)

    def test_not_equal_when_status_differs(self):
        metadata = ProjectMetadata()
        a = Project(project_id="p1", status=ProjectStatus.PLANNING, metadata=metadata)
        b = Project(project_id="p1", status=ProjectStatus.ACTIVE, metadata=metadata)
        self.assertNotEqual(a, b)


if __name__ == "__main__":
    unittest.main()
