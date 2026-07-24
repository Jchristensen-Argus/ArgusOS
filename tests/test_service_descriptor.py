"""Unit tests for argus.services.service_descriptor."""

import unittest
from dataclasses import FrozenInstanceError

from argus.services.service_descriptor import ServiceDescriptor, ServiceState


class FakeInterface:
    pass


class FakeService(FakeInterface):
    pass


def _descriptor(**overrides):
    defaults = dict(
        name="fake_service",
        instance=FakeService(),
        interface=FakeInterface,
        version="1.0.0",
        state=ServiceState.REGISTERED,
    )
    defaults.update(overrides)
    return ServiceDescriptor(**defaults)


class ServiceDescriptorTests(unittest.TestCase):
    def test_fields_are_stored(self):
        instance = FakeService()
        descriptor = _descriptor(instance=instance)

        self.assertEqual(descriptor.name, "fake_service")
        self.assertIs(descriptor.instance, instance)
        self.assertIs(descriptor.interface, FakeInterface)
        self.assertEqual(descriptor.version, "1.0.0")
        self.assertEqual(descriptor.state, ServiceState.REGISTERED)

    def test_metadata_defaults_to_empty_mapping(self):
        descriptor = _descriptor()

        self.assertEqual(dict(descriptor.metadata), {})

    def test_metadata_values_are_preserved(self):
        descriptor = _descriptor(metadata={"owner": "argus-factory"})

        self.assertEqual(descriptor.metadata["owner"], "argus-factory")

    def test_descriptor_is_frozen(self):
        descriptor = _descriptor()

        with self.assertRaises(FrozenInstanceError):
            descriptor.name = "changed"

    def test_metadata_mapping_cannot_be_mutated(self):
        descriptor = _descriptor(metadata={"key": "value"})

        with self.assertRaises(TypeError):
            descriptor.metadata["key"] = "changed"

    def test_default_metadata_mapping_cannot_be_mutated(self):
        descriptor = _descriptor()

        with self.assertRaises(TypeError):
            descriptor.metadata["key"] = "value"

    def test_service_state_has_expected_members(self):
        self.assertEqual(
            {member.name for member in ServiceState},
            {"REGISTERED", "ACTIVE", "STOPPED"},
        )


if __name__ == "__main__":
    unittest.main()
