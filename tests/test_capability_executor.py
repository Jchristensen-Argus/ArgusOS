"""Unit tests for argus.capability_executor.executor.CapabilityExecutor."""

import dataclasses
import logging
import unittest

from argus.capability import Capability, CapabilityRegistry, ICapabilityRegistry
from argus.capability_executor import (
    CapabilityExecutionError,
    CapabilityExecutionStatus,
    CapabilityExecutor,
    ICapabilityExecutor,
    InvalidTaskReferenceError,
)
from argus.events import InMemoryEventBus
from argus.intent import IntentType
from argus.lifecycle import IService
from argus.lifecycle.lifecycle import LifecycleState
from argus.task import Task


def _silent_logger() -> logging.Logger:
    logger = logging.getLogger("test_capability_executor")
    logger.addHandler(logging.NullHandler())
    logger.propagate = False
    return logger


def _capability_registry() -> CapabilityRegistry:
    return CapabilityRegistry(event_bus=InMemoryEventBus(logger=_silent_logger()))


def _capability(**kwargs) -> Capability:
    defaults = dict(
        name="Do Thing",
        description="d",
        intent_types=(IntentType.UNKNOWN,),
        action_kind="workflow",
        workflow_id="w",
    )
    defaults.update(kwargs)
    return Capability(**defaults)


def _executor(capability_registry=None) -> CapabilityExecutor:
    return CapabilityExecutor(capability_registry=capability_registry or _capability_registry())


# -- identity / IService ----------------------------------------------


class CapabilityExecutorIdentityTests(unittest.TestCase):
    def test_is_an_icapabilityexecutor(self):
        self.assertIsInstance(_executor(), ICapabilityExecutor)

    def test_is_an_iservice(self):
        self.assertIsInstance(_executor(), IService)

    def test_starts_in_created_state(self):
        self.assertEqual(_executor().status(), LifecycleState.CREATED)

    def test_constructor_requires_capability_registry(self):
        with self.assertRaises(TypeError):
            CapabilityExecutor()  # type: ignore[call-arg]


# -- constructor injection -----------------------------------------------


class ConstructorInjectionTests(unittest.TestCase):
    def test_capability_registry_is_stored(self):
        registry = _capability_registry()
        executor = CapabilityExecutor(capability_registry=registry)
        self.assertIs(executor._capability_registry, registry)

    def test_accepts_any_icapabilityregistry_implementation(self):
        registry = _capability_registry()
        executor = CapabilityExecutor(capability_registry=registry)
        self.assertIsInstance(executor, CapabilityExecutor)
        self.assertIsInstance(registry, ICapabilityRegistry)

    def test_executor_holds_exactly_state_and_capability_registry(self):
        registry = _capability_registry()
        executor = CapabilityExecutor(capability_registry=registry)
        self.assertEqual(
            vars(executor),
            {"_capability_registry": registry, "_state": LifecycleState.CREATED},
        )


# -- lifecycle ----------------------------------------------------------


class CapabilityExecutorLifecycleTests(unittest.TestCase):
    def test_initialize_transitions_to_initializing(self):
        executor = _executor()
        executor.initialize()
        self.assertEqual(executor.status(), LifecycleState.INITIALIZING)

    def test_initialize_twice_raises(self):
        executor = _executor()
        executor.initialize()
        with self.assertRaises(CapabilityExecutionError):
            executor.initialize()

    def test_start_requires_initializing(self):
        executor = _executor()
        with self.assertRaises(CapabilityExecutionError):
            executor.start()

    def test_start_transitions_to_running(self):
        executor = _executor()
        executor.initialize()
        executor.start()
        self.assertEqual(executor.status(), LifecycleState.RUNNING)

    def test_stop_requires_running(self):
        executor = _executor()
        with self.assertRaises(CapabilityExecutionError):
            executor.stop()

    def test_stop_transitions_to_stopped(self):
        executor = _executor()
        executor.initialize()
        executor.start()
        executor.stop()
        self.assertEqual(executor.status(), LifecycleState.STOPPED)

    def test_status_reflects_current_state_throughout(self):
        executor = _executor()
        self.assertEqual(executor.status(), LifecycleState.CREATED)
        executor.initialize()
        self.assertEqual(executor.status(), LifecycleState.INITIALIZING)
        executor.start()
        self.assertEqual(executor.status(), LifecycleState.RUNNING)
        executor.stop()
        self.assertEqual(executor.status(), LifecycleState.STOPPED)


# -- resolve() is never gated --------------------------------------------


class UngatedBehaviorTests(unittest.TestCase):
    def test_resolve_works_in_created_state(self):
        executor = _executor()
        self.assertEqual(executor.status(), LifecycleState.CREATED)
        result = executor.resolve(Task(name="A"))
        self.assertEqual(result.status, CapabilityExecutionStatus.NOT_FOUND)

    def test_resolve_works_while_running(self):
        executor = _executor()
        executor.initialize()
        executor.start()
        result = executor.resolve(Task(name="A"))
        self.assertEqual(result.status, CapabilityExecutionStatus.NOT_FOUND)

    def test_resolve_works_after_stopped(self):
        executor = _executor()
        executor.initialize()
        executor.start()
        executor.stop()
        result = executor.resolve(Task(name="A"))
        self.assertEqual(result.status, CapabilityExecutionStatus.NOT_FOUND)


# -- exact-name resolution ------------------------------------------------


class ExactNameResolutionTests(unittest.TestCase):
    def test_matching_name_returns_completed_with_the_capability(self):
        registry = _capability_registry()
        capability = _capability(name="Send Email")
        registry.register(capability)
        executor = CapabilityExecutor(capability_registry=registry)

        result = executor.resolve(Task(name="Send Email"))

        self.assertEqual(result.status, CapabilityExecutionStatus.COMPLETED)
        self.assertIs(result.capability, capability)

    def test_matching_is_exact_not_partial(self):
        registry = _capability_registry()
        registry.register(_capability(name="Send Email"))
        executor = CapabilityExecutor(capability_registry=registry)

        result = executor.resolve(Task(name="Send Email To Bob"))

        self.assertEqual(result.status, CapabilityExecutionStatus.NOT_FOUND)

    def test_matching_is_case_sensitive(self):
        registry = _capability_registry()
        registry.register(_capability(name="Send Email"))
        executor = CapabilityExecutor(capability_registry=registry)

        result = executor.resolve(Task(name="send email"))

        self.assertEqual(result.status, CapabilityExecutionStatus.NOT_FOUND)

    def test_result_task_is_the_task_that_was_resolved(self):
        registry = _capability_registry()
        registry.register(_capability(name="Send Email"))
        executor = CapabilityExecutor(capability_registry=registry)
        task = Task(name="Send Email")

        result = executor.resolve(task)

        self.assertIs(result.task, task)


# -- not-found behavior ----------------------------------------------------


class NotFoundResolutionTests(unittest.TestCase):
    def test_empty_registry_returns_not_found(self):
        executor = _executor()
        result = executor.resolve(Task(name="Anything"))
        self.assertEqual(result.status, CapabilityExecutionStatus.NOT_FOUND)
        self.assertIsNone(result.capability)

    def test_non_matching_name_returns_not_found(self):
        registry = _capability_registry()
        registry.register(_capability(name="Send Email"))
        executor = CapabilityExecutor(capability_registry=registry)

        result = executor.resolve(Task(name="Send SMS"))

        self.assertEqual(result.status, CapabilityExecutionStatus.NOT_FOUND)
        self.assertIsNone(result.capability)

    def test_empty_task_name_returns_not_found(self):
        executor = _executor()
        result = executor.resolve(Task())
        self.assertEqual(result.status, CapabilityExecutionStatus.NOT_FOUND)

    def test_no_exception_is_raised_for_a_not_found_task(self):
        # CapabilityNotFoundError is a normal resolution outcome, not
        # an error to propagate - see executor.py's own module
        # docstring.
        executor = _executor()
        try:
            executor.resolve(Task(name="Anything"))
        except Exception as error:  # pragma: no cover - failure path
            self.fail(f"resolve() raised unexpectedly: {error}")


# -- registry lookup --------------------------------------------------------


class RegistryLookupTests(unittest.TestCase):
    def test_resolve_calls_get_by_name_with_the_task_name(self):
        calls = []

        class _SpyRegistry:
            def get_by_name(self, name):
                calls.append(name)
                from argus.capability.exceptions import CapabilityNotFoundError

                raise CapabilityNotFoundError(f"no capability named {name!r}")

        executor = CapabilityExecutor(capability_registry=_SpyRegistry())
        executor.resolve(Task(name="Send Email"))

        self.assertEqual(calls, ["Send Email"])

    def test_resolve_never_calls_any_other_registry_method(self):
        # "Only deterministic resolution" - resolve() only ever calls
        # get_by_name(), never register()/unregister()/get()/
        # find_by_intent_type()/list_capabilities()/contains().
        class _ExplodingExceptGetByName:
            def get_by_name(self, name):
                from argus.capability.exceptions import CapabilityNotFoundError

                raise CapabilityNotFoundError(f"no capability named {name!r}")

            def __getattr__(self, name):
                raise AssertionError(
                    f"CapabilityExecutor.resolve() must never call "
                    f"CapabilityRegistry.{name}()."
                )

        executor = CapabilityExecutor(capability_registry=_ExplodingExceptGetByName())
        result = executor.resolve(Task(name="Anything"))
        self.assertEqual(result.status, CapabilityExecutionStatus.NOT_FOUND)


# -- invalid Task ------------------------------------------------------------


class InvalidTaskTests(unittest.TestCase):
    def test_non_task_argument_raises(self):
        executor = _executor()
        with self.assertRaises(InvalidTaskReferenceError):
            executor.resolve("not a task")

    def test_none_argument_raises(self):
        executor = _executor()
        with self.assertRaises(InvalidTaskReferenceError):
            executor.resolve(None)

    def test_dict_masquerading_as_task_raises(self):
        executor = _executor()
        with self.assertRaises(InvalidTaskReferenceError):
            executor.resolve({"name": "Send Email"})


# -- immutable result / no mutation of inputs ----------------------------


class ImmutableResultTests(unittest.TestCase):
    def test_result_cannot_be_mutated(self):
        executor = _executor()
        result = executor.resolve(Task(name="A"))
        with self.assertRaises(dataclasses.FrozenInstanceError):
            result.status = CapabilityExecutionStatus.COMPLETED

    def test_task_is_never_mutated(self):
        executor = _executor()
        task = Task(name="A")
        before = dataclasses.replace(task)
        executor.resolve(task)
        self.assertEqual(task, before)

    def test_multiple_resolutions_of_the_same_task_produce_independent_results(self):
        executor = _executor()
        task = Task(name="A")
        first = executor.resolve(task)
        second = executor.resolve(task)
        self.assertNotEqual(first.execution_id, second.execution_id)
        self.assertEqual(first.status, second.status)

    def test_found_capability_is_never_invoked(self):
        # "No Capability invocation" - Capability itself exposes no
        # callable behavior for resolve() to invoke; confirmed simply
        # by the returned Capability being the exact same, unmodified
        # instance as the one registered.
        registry = _capability_registry()
        capability = _capability(name="Send Email")
        registry.register(capability)
        executor = CapabilityExecutor(capability_registry=registry)

        result = executor.resolve(Task(name="Send Email"))

        self.assertIs(result.capability, capability)


if __name__ == "__main__":
    unittest.main()
