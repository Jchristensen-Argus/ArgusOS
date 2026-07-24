"""Unit tests for argus.lifecycle (LifecycleState, LifecycleManager)."""

import unittest

from argus.lifecycle.exceptions import InvalidStateTransitionError, LifecycleError
from argus.lifecycle.lifecycle import LifecycleManager, LifecycleState


class LifecycleStateTests(unittest.TestCase):
    def test_expected_members_exist(self):
        self.assertEqual(
            {member.name for member in LifecycleState},
            {
                "CREATED",
                "REGISTERED",
                "INITIALIZING",
                "RUNNING",
                "STOPPING",
                "STOPPED",
                "FAILED",
            },
        )

    def test_members_have_unique_values(self):
        values = [member.value for member in LifecycleState]

        self.assertEqual(len(values), len(set(values)))


class RegisterTests(unittest.TestCase):
    def test_register_sets_registered_state(self):
        manager = LifecycleManager()

        manager.register("svc")

        self.assertEqual(manager.status("svc"), LifecycleState.REGISTERED)

    def test_register_twice_raises(self):
        manager = LifecycleManager()
        manager.register("svc")

        with self.assertRaises(InvalidStateTransitionError):
            manager.register("svc")

    def test_register_rejects_empty_name(self):
        manager = LifecycleManager()

        with self.assertRaises(LifecycleError):
            manager.register("")


class InitializeTests(unittest.TestCase):
    def test_initialize_sets_initializing_state(self):
        manager = LifecycleManager()
        manager.register("svc")

        manager.initialize("svc")

        self.assertEqual(manager.status("svc"), LifecycleState.INITIALIZING)

    def test_initialize_without_register_raises(self):
        manager = LifecycleManager()

        with self.assertRaises(InvalidStateTransitionError):
            manager.initialize("svc")

    def test_initialize_twice_raises(self):
        manager = LifecycleManager()
        manager.register("svc")
        manager.initialize("svc")

        with self.assertRaises(InvalidStateTransitionError):
            manager.initialize("svc")


class StartTests(unittest.TestCase):
    def test_start_sets_running_state(self):
        manager = LifecycleManager()
        manager.register("svc")
        manager.initialize("svc")

        manager.start("svc")

        self.assertEqual(manager.status("svc"), LifecycleState.RUNNING)

    def test_start_without_initialize_raises(self):
        manager = LifecycleManager()
        manager.register("svc")

        with self.assertRaises(InvalidStateTransitionError):
            manager.start("svc")


class StopTests(unittest.TestCase):
    def test_stop_sets_stopped_state(self):
        manager = LifecycleManager()
        manager.register("svc")
        manager.initialize("svc")
        manager.start("svc")

        manager.stop("svc")

        self.assertEqual(manager.status("svc"), LifecycleState.STOPPED)

    def test_stop_without_running_raises(self):
        manager = LifecycleManager()
        manager.register("svc")

        with self.assertRaises(InvalidStateTransitionError):
            manager.stop("svc")

    def test_stop_twice_raises(self):
        manager = LifecycleManager()
        manager.register("svc")
        manager.initialize("svc")
        manager.start("svc")
        manager.stop("svc")

        with self.assertRaises(InvalidStateTransitionError):
            manager.stop("svc")


class StatusTests(unittest.TestCase):
    def test_status_of_unregistered_service_raises_lifecycle_error(self):
        manager = LifecycleManager()

        with self.assertRaises(LifecycleError):
            manager.status("missing")

    def test_status_reflects_each_step_of_the_happy_path(self):
        manager = LifecycleManager()
        manager.register("svc")
        self.assertEqual(manager.status("svc"), LifecycleState.REGISTERED)

        manager.initialize("svc")
        self.assertEqual(manager.status("svc"), LifecycleState.INITIALIZING)

        manager.start("svc")
        self.assertEqual(manager.status("svc"), LifecycleState.RUNNING)

        manager.stop("svc")
        self.assertEqual(manager.status("svc"), LifecycleState.STOPPED)


class FailTests(unittest.TestCase):
    def test_fail_from_running_sets_failed_state(self):
        manager = LifecycleManager()
        manager.register("svc")
        manager.initialize("svc")
        manager.start("svc")

        manager.fail("svc")

        self.assertEqual(manager.status("svc"), LifecycleState.FAILED)

    def test_fail_from_registered_sets_failed_state(self):
        manager = LifecycleManager()
        manager.register("svc")

        manager.fail("svc")

        self.assertEqual(manager.status("svc"), LifecycleState.FAILED)

    def test_fail_unregistered_service_raises(self):
        manager = LifecycleManager()

        with self.assertRaises(InvalidStateTransitionError):
            manager.fail("missing")

    def test_fail_already_stopped_raises(self):
        manager = LifecycleManager()
        manager.register("svc")
        manager.initialize("svc")
        manager.start("svc")
        manager.stop("svc")

        with self.assertRaises(InvalidStateTransitionError):
            manager.fail("svc")

    def test_fail_twice_raises(self):
        manager = LifecycleManager()
        manager.register("svc")
        manager.fail("svc")

        with self.assertRaises(InvalidStateTransitionError):
            manager.fail("svc")


class InvalidTransitionExamplesTests(unittest.TestCase):
    """The three illegal transitions called out explicitly in
    factory/packages/005_SERVICE_LIFECYCLE.md."""

    def test_running_to_initializing_raises(self):
        manager = LifecycleManager()
        manager.register("svc")
        manager.initialize("svc")
        manager.start("svc")

        with self.assertRaises(InvalidStateTransitionError):
            manager.initialize("svc")

    def test_stopped_to_running_raises(self):
        manager = LifecycleManager()
        manager.register("svc")
        manager.initialize("svc")
        manager.start("svc")
        manager.stop("svc")

        with self.assertRaises(InvalidStateTransitionError):
            manager.start("svc")

    def test_created_to_running_raises(self):
        manager = LifecycleManager()

        with self.assertRaises(InvalidStateTransitionError):
            manager.start("never-registered")


class ManagerIsolationTests(unittest.TestCase):
    def test_services_are_tracked_independently(self):
        manager = LifecycleManager()
        manager.register("a")
        manager.register("b")
        manager.initialize("a")

        self.assertEqual(manager.status("a"), LifecycleState.INITIALIZING)
        self.assertEqual(manager.status("b"), LifecycleState.REGISTERED)


if __name__ == "__main__":
    unittest.main()
