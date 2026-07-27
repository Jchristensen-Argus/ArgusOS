"""Unit tests for argus.workspace.workspace.Workspace."""

import copy
import dataclasses
import pickle
import unittest

from argus.workspace import Workspace, WorkspaceMetadata, WorkspaceStatus


class DefaultsTests(unittest.TestCase):
    def test_defaults(self):
        workspace = Workspace()
        self.assertTrue(workspace.workspace_id)
        self.assertEqual(workspace.name, "")
        self.assertEqual(workspace.description, "")
        self.assertEqual(workspace.status, WorkspaceStatus.ACTIVE)
        self.assertIsInstance(workspace.metadata, WorkspaceMetadata)

    def test_all_fields_set(self):
        metadata = WorkspaceMetadata(extra={"k": "v"})
        workspace = Workspace(
            workspace_id="fixed-id",
            name="Joel Christensen",
            description="Personal workspace",
            status=WorkspaceStatus.INACTIVE,
            metadata=metadata,
        )
        self.assertEqual(workspace.workspace_id, "fixed-id")
        self.assertEqual(workspace.name, "Joel Christensen")
        self.assertEqual(workspace.description, "Personal workspace")
        self.assertEqual(workspace.status, WorkspaceStatus.INACTIVE)
        self.assertIs(workspace.metadata, metadata)

    def test_default_workspace_id_is_unique_per_instance(self):
        a = Workspace()
        b = Workspace()
        self.assertNotEqual(a.workspace_id, b.workspace_id)


class FieldOrderTests(unittest.TestCase):
    def test_field_order_places_metadata_last(self):
        field_names = [f.name for f in dataclasses.fields(Workspace)]
        self.assertEqual(
            field_names, ["workspace_id", "name", "description", "status", "metadata"]
        )


class ExampleNamesTests(unittest.TestCase):
    def test_accepts_every_example_name_from_the_work_order(self):
        # "Examples: Joel Christensen, Deline Box & Display, Just
        # Tallow, Family, Sandbox."
        for name in (
            "Joel Christensen",
            "Deline Box & Display",
            "Just Tallow",
            "Family",
            "Sandbox",
        ):
            workspace = Workspace(name=name)
            self.assertEqual(workspace.name, name)


class DefaultStatusTests(unittest.TestCase):
    def test_default_status_is_active(self):
        # Unlike ProjectStatus's own PLANNING default (036),
        # WorkspaceStatus's own first-listed member is ACTIVE - see
        # status.py's own module docstring for why.
        self.assertEqual(Workspace().status, WorkspaceStatus.ACTIVE)


class ImmutabilityTests(unittest.TestCase):
    def test_immutability(self):
        workspace = Workspace()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            workspace.workspace_id = "mutated"

    def test_name_field_immutable(self):
        workspace = Workspace()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            workspace.name = "mutated"

    def test_metadata_field_immutable(self):
        workspace = Workspace()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            workspace.metadata = WorkspaceMetadata()


class MiscellaneousRobustnessTests(unittest.TestCase):
    def test_deepcopy_of_scalar_fields_round_trips_equal(self):
        workspace = Workspace()
        copied_id = copy.deepcopy(workspace.workspace_id)
        self.assertEqual(copied_id, workspace.workspace_id)

    def test_pickle_of_scalar_fields_round_trips_equal(self):
        workspace = Workspace()
        self.assertEqual(
            pickle.loads(pickle.dumps(workspace.workspace_id)), workspace.workspace_id
        )
        self.assertIs(pickle.loads(pickle.dumps(workspace.status)), workspace.status)

    def test_workspace_id_is_a_plain_string_suitable_for_json(self):
        workspace = Workspace()
        self.assertIsInstance(workspace.workspace_id, str)


class EqualityTests(unittest.TestCase):
    def test_equality_when_all_fields_match(self):
        metadata = WorkspaceMetadata()
        a = Workspace(workspace_id="w1", name="ArgusOS", metadata=metadata)
        b = Workspace(workspace_id="w1", name="ArgusOS", metadata=metadata)
        self.assertEqual(a, b)

    def test_not_equal_when_workspace_id_differs(self):
        metadata = WorkspaceMetadata()
        a = Workspace(workspace_id="w1", metadata=metadata)
        b = Workspace(workspace_id="w2", metadata=metadata)
        self.assertNotEqual(a, b)

    def test_not_equal_when_status_differs(self):
        metadata = WorkspaceMetadata()
        a = Workspace(workspace_id="w1", status=WorkspaceStatus.ACTIVE, metadata=metadata)
        b = Workspace(workspace_id="w1", status=WorkspaceStatus.ARCHIVED, metadata=metadata)
        self.assertNotEqual(a, b)


if __name__ == "__main__":
    unittest.main()
