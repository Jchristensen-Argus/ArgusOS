"""Unit tests for argus.scheduler.scheduler.Scheduler."""

import logging
import unittest
from datetime import datetime, timedelta, timezone

from argus.events import EventType, InMemoryEventBus
from argus.lifecycle import LifecycleManager, LifecycleState
from argus.scheduler import (
    DailyTrigger,
    IntervalTrigger,
    InvalidTrigger,
    OneShotTrigger,
    Scheduler,
    SchedulerError,
    TaskAlreadyExists,
    TaskNotFound,
    TaskPriority,
)


def _silent_logger() -> logging.Logger:
    logger = logging.getLogger("test_scheduler")
    logger.addHandler(logging.NullHandler())
    logger.propagate = False
    return logger


NOW = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)


class SchedulerTestCase(unittest.TestCase):
    """Common setup: a started Scheduler with an in-memory Event Bus
    recording every published event, keyed by EventType."""

    def setUp(self):
        self.event_bus = InMemoryEventBus(logger=_silent_logger())
        self.received = []
        for event_type in EventType:
            self.event_bus.subscribe(event_type, self._record)
        self.scheduler = Scheduler(event_bus=self.event_bus)
        self.scheduler.initialize()
        self.scheduler.start()

    def _record(self, event):
        self.received.append(event)

    def _events_of(self, event_type):
        return [event for event in self.received if event.type == event_type]


# -- IService lifecycle ---------------------------------------------------


class SchedulerIServiceTests(unittest.TestCase):
    def setUp(self):
        self.event_bus = InMemoryEventBus(logger=_silent_logger())
        self.scheduler = Scheduler(event_bus=self.event_bus)

    def test_initial_status_is_created(self):
        self.assertEqual(self.scheduler.status(), LifecycleState.CREATED)

    def test_initialize_transitions_to_initializing(self):
        self.scheduler.initialize()

        self.assertEqual(self.scheduler.status(), LifecycleState.INITIALIZING)

    def test_start_transitions_to_running(self):
        self.scheduler.initialize()
        self.scheduler.start()

        self.assertEqual(self.scheduler.status(), LifecycleState.RUNNING)

    def test_stop_transitions_to_stopped(self):
        self.scheduler.initialize()
        self.scheduler.start()
        self.scheduler.stop()

        self.assertEqual(self.scheduler.status(), LifecycleState.STOPPED)

    def test_start_before_initialize_raises(self):
        with self.assertRaises(SchedulerError):
            self.scheduler.start()

    def test_initialize_twice_raises(self):
        self.scheduler.initialize()

        with self.assertRaises(SchedulerError):
            self.scheduler.initialize()

    def test_stop_before_start_raises(self):
        self.scheduler.initialize()

        with self.assertRaises(SchedulerError):
            self.scheduler.stop()

    def test_tick_before_start_raises_scheduler_error(self):
        with self.assertRaises(SchedulerError):
            self.scheduler.tick(now=NOW)

    def test_tick_after_stop_raises_scheduler_error(self):
        self.scheduler.initialize()
        self.scheduler.start()
        self.scheduler.stop()

        with self.assertRaises(SchedulerError):
            self.scheduler.tick(now=NOW)

    def test_registry_operations_work_before_start(self):
        # schedule/get_task/list_tasks are pure registry operations,
        # unaffected by IService lifecycle state - only tick() is gated.
        task = self.scheduler.schedule(
            name="a", callback=lambda: None, trigger=OneShotTrigger(run_at=NOW + timedelta(seconds=1)), now=NOW)

        self.assertEqual(self.scheduler.get_task(task.id), task)
        self.assertEqual(len(self.scheduler.list_tasks()), 1)


class IServiceLifecycleDivergenceTests(unittest.TestCase):
    """Empirically confirms (or refutes) the duplicate-state concern
    raised in ADR-0002 (design/decisions/0002_ISERVICE_ADOPTION_CRITERION.md):
    Scheduler tracks its own LifecycleState to satisfy IService.status(),
    entirely independent of whatever a LifecycleManager tracks for the
    same registered name. This test demonstrates that the two can be
    driven out of sync, because nothing enforces that a call to
    scheduler.start() is paired with a call to
    lifecycle_manager.start('scheduler')."""

    def test_schedulers_own_state_can_diverge_from_lifecycle_manager_state(self):
        event_bus = InMemoryEventBus(logger=_silent_logger())
        scheduler = Scheduler(event_bus=event_bus)
        lifecycle_manager = LifecycleManager()

        # bootstrap.py's actual behavior: register only.
        lifecycle_manager.register("scheduler")
        self.assertEqual(lifecycle_manager.status("scheduler"), LifecycleState.REGISTERED)
        self.assertEqual(scheduler.status(), LifecycleState.CREATED)

        # A caller exercises Scheduler's own IService lifecycle
        # directly (e.g. to actually use tick()), without a
        # corresponding call into the Lifecycle Manager.
        scheduler.initialize()
        scheduler.start()

        # The two trackers of "what state is the Scheduler in" now
        # disagree: LifecycleManager still says REGISTERED, while the
        # object itself says RUNNING. This is the exact failure mode
        # ADR-0002 predicted for any IService adopter.
        self.assertEqual(lifecycle_manager.status("scheduler"), LifecycleState.REGISTERED)
        self.assertEqual(scheduler.status(), LifecycleState.RUNNING)
        self.assertNotEqual(
            lifecycle_manager.status("scheduler"),
            scheduler.status(),
            "Expected divergence: this confirms ADR-0002's concern empirically.",
        )


# -- schedule / duplicate IDs / validation --------------------------------


class ScheduleTests(SchedulerTestCase):
    def test_schedule_returns_task_with_computed_next_run(self):
        run_at = NOW + timedelta(minutes=5)

        task = self.scheduler.schedule(
            name="a", callback=lambda: None, trigger=OneShotTrigger(run_at=run_at), now=NOW)

        self.assertEqual(task.next_run, run_at)

    def test_schedule_generates_id_when_not_given(self):
        task = self.scheduler.schedule(
            name="a", callback=lambda: None, trigger=OneShotTrigger(run_at=NOW + timedelta(seconds=1)), now=NOW)

        self.assertTrue(task.id)

    def test_schedule_honors_explicit_task_id(self):
        task = self.scheduler.schedule(
            name="a", callback=lambda: None, trigger=OneShotTrigger(run_at=NOW + timedelta(seconds=1)), task_id="fixed", now=NOW)

        self.assertEqual(task.id, "fixed")

    def test_schedule_duplicate_task_id_raises_task_already_exists(self):
        self.scheduler.schedule(
            name="a", callback=lambda: None, trigger=OneShotTrigger(run_at=NOW + timedelta(seconds=1)), task_id="dup", now=NOW)

        with self.assertRaises(TaskAlreadyExists):
            self.scheduler.schedule(
                name="b", callback=lambda: None, trigger=OneShotTrigger(run_at=NOW + timedelta(seconds=1)), task_id="dup", now=NOW)

    def test_schedule_rejects_empty_name(self):
        with self.assertRaises(SchedulerError):
            self.scheduler.schedule(
                name="", callback=lambda: None, trigger=OneShotTrigger(run_at=NOW + timedelta(seconds=1)), now=NOW)

    def test_schedule_rejects_non_callable_callback(self):
        with self.assertRaises(SchedulerError):
            self.scheduler.schedule(name="a", callback="not-callable", trigger=OneShotTrigger(run_at=NOW + timedelta(seconds=1)), now=NOW)

    def test_schedule_rejects_non_trigger(self):
        with self.assertRaises(InvalidTrigger):
            self.scheduler.schedule(name="a", callback=lambda: None, trigger="not-a-trigger", now=NOW)

    def test_schedule_publishes_task_scheduled_event(self):
        task = self.scheduler.schedule(
            name="a", callback=lambda: None, trigger=OneShotTrigger(run_at=NOW + timedelta(seconds=1)), now=NOW)

        events = self._events_of(EventType.TASK_SCHEDULED)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].payload["task_id"], task.id)
        self.assertEqual(events[0].payload["task_name"], "a")
        self.assertEqual(events[0].source, "scheduler")


# -- cancel -----------------------------------------------------------------


class CancelTests(SchedulerTestCase):
    def test_cancel_removes_task(self):
        task = self.scheduler.schedule(
            name="a", callback=lambda: None, trigger=OneShotTrigger(run_at=NOW + timedelta(seconds=1)), now=NOW)

        self.scheduler.cancel(task.id)

        with self.assertRaises(TaskNotFound):
            self.scheduler.get_task(task.id)

    def test_cancel_missing_task_raises_task_not_found(self):
        with self.assertRaises(TaskNotFound):
            self.scheduler.cancel("missing")

    def test_cancel_publishes_task_cancelled_event(self):
        task = self.scheduler.schedule(
            name="a", callback=lambda: None, trigger=OneShotTrigger(run_at=NOW + timedelta(seconds=1)), now=NOW)

        self.scheduler.cancel(task.id)

        events = self._events_of(EventType.TASK_CANCELLED)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].payload["task_id"], task.id)

    def test_cancelled_id_can_be_reused(self):
        task = self.scheduler.schedule(
            name="a", callback=lambda: None, trigger=OneShotTrigger(run_at=NOW + timedelta(seconds=1)), task_id="x", now=NOW)
        self.scheduler.cancel(task.id)

        reused = self.scheduler.schedule(
            name="b", callback=lambda: None, trigger=OneShotTrigger(run_at=NOW + timedelta(seconds=1)), task_id="x", now=NOW)

        self.assertEqual(reused.id, "x")


# -- pause / resume -----------------------------------------------------


class PauseResumeTests(SchedulerTestCase):
    def test_pause_disables_task(self):
        task = self.scheduler.schedule(
            name="a", callback=lambda: None, trigger=OneShotTrigger(run_at=NOW + timedelta(seconds=1)), now=NOW)

        self.scheduler.pause(task.id)

        self.assertFalse(self.scheduler.get_task(task.id).enabled)

    def test_pause_missing_task_raises_task_not_found(self):
        with self.assertRaises(TaskNotFound):
            self.scheduler.pause("missing")

    def test_pause_publishes_task_paused_event(self):
        task = self.scheduler.schedule(
            name="a", callback=lambda: None, trigger=OneShotTrigger(run_at=NOW + timedelta(seconds=1)), now=NOW)

        self.scheduler.pause(task.id)

        events = self._events_of(EventType.TASK_PAUSED)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].payload["task_id"], task.id)

    def test_paused_task_is_not_executed_on_tick(self):
        calls = []
        task = self.scheduler.schedule(
            name="a", callback=lambda: calls.append(1), trigger=OneShotTrigger(run_at=NOW + timedelta(seconds=1)), now=NOW)
        self.scheduler.pause(task.id)

        executed = self.scheduler.tick(now=NOW + timedelta(seconds=1))

        self.assertEqual(executed, 0)
        self.assertEqual(calls, [])

    def test_resume_re_enables_task(self):
        task = self.scheduler.schedule(
            name="a", callback=lambda: None, trigger=OneShotTrigger(run_at=NOW + timedelta(seconds=1)), now=NOW)
        self.scheduler.pause(task.id)

        self.scheduler.resume(task.id)

        self.assertTrue(self.scheduler.get_task(task.id).enabled)

    def test_resume_missing_task_raises_task_not_found(self):
        with self.assertRaises(TaskNotFound):
            self.scheduler.resume("missing")

    def test_resume_publishes_task_resumed_event(self):
        task = self.scheduler.schedule(
            name="a", callback=lambda: None, trigger=OneShotTrigger(run_at=NOW + timedelta(seconds=1)), now=NOW)
        self.scheduler.pause(task.id)

        self.scheduler.resume(task.id)

        events = self._events_of(EventType.TASK_RESUMED)
        self.assertEqual(len(events), 1)

    def test_resume_recomputes_next_run_from_current_time(self):
        # Scheduled at NOW, then paused and resumed an hour "later":
        # next_run should be recomputed relative to the resume-time
        # `now` passed in, not preserved from before pause().
        trigger = IntervalTrigger(interval_seconds=60)
        task = self.scheduler.schedule(name="a", callback=lambda: None, trigger=trigger, now=NOW)
        self.scheduler.pause(task.id)

        resume_time = NOW + timedelta(hours=1)
        self.scheduler.resume(task.id, now=resume_time)

        expected_next_run = resume_time + timedelta(seconds=60)
        self.assertEqual(self.scheduler.get_task(task.id).next_run, expected_next_run)
        self.assertGreater(self.scheduler.get_task(task.id).next_run, task.next_run)


# -- tick / trigger execution --------------------------------------------


class TickTests(SchedulerTestCase):
    def test_tick_executes_due_one_shot_task(self):
        calls = []
        self.scheduler.schedule(
            name="a", callback=lambda: calls.append("a"), trigger=OneShotTrigger(run_at=NOW + timedelta(seconds=1)), now=NOW)

        executed = self.scheduler.tick(now=NOW + timedelta(seconds=1))

        self.assertEqual(executed, 1)
        self.assertEqual(calls, ["a"])

    def test_tick_skips_not_yet_due_task(self):
        calls = []
        self.scheduler.schedule(
            name="a",
            callback=lambda: calls.append("a"),
            trigger=OneShotTrigger(run_at=NOW + timedelta(hours=1)), now=NOW,)

        executed = self.scheduler.tick(now=NOW)

        self.assertEqual(executed, 0)
        self.assertEqual(calls, [])

    def test_one_shot_task_does_not_fire_twice(self):
        calls = []
        self.scheduler.schedule(
            name="a", callback=lambda: calls.append("a"), trigger=OneShotTrigger(run_at=NOW + timedelta(seconds=1)), now=NOW)

        self.scheduler.tick(now=NOW + timedelta(seconds=1))
        second_executed = self.scheduler.tick(now=NOW + timedelta(hours=1))

        self.assertEqual(second_executed, 0)
        self.assertEqual(calls, ["a"])

    def test_interval_task_fires_repeatedly(self):
        calls = []
        self.scheduler.schedule(
            name="a", callback=lambda: calls.append("a"), trigger=IntervalTrigger(interval_seconds=10), now=NOW)

        self.scheduler.tick(now=NOW + timedelta(seconds=10))
        self.scheduler.tick(now=NOW + timedelta(seconds=20))
        self.scheduler.tick(now=NOW + timedelta(seconds=30))

        self.assertEqual(calls, ["a", "a", "a"])

    def test_daily_task_fires_once_per_day(self):
        calls = []
        self.scheduler.schedule(
            name="a",
            callback=lambda: calls.append("a"),
            trigger=DailyTrigger(hour=12, minute=0), now=NOW,)

        # First fire is "today" (NOW is exactly 12:00:00, so the first
        # due instant is tomorrow at 12:00 per strict-> semantics).
        self.scheduler.tick(now=NOW + timedelta(days=1))
        self.scheduler.tick(now=NOW + timedelta(days=1, hours=1))  # not due again yet
        self.scheduler.tick(now=NOW + timedelta(days=2))

        self.assertEqual(calls, ["a", "a"])

    def test_tick_updates_last_run(self):
        task = self.scheduler.schedule(
            name="a", callback=lambda: None, trigger=OneShotTrigger(run_at=NOW + timedelta(seconds=1)), now=NOW)
        tick_time = NOW + timedelta(seconds=1)

        self.scheduler.tick(now=tick_time)

        self.assertEqual(self.scheduler.get_task(task.id).last_run, tick_time)

    def test_tick_publishes_task_started_and_task_completed(self):
        task = self.scheduler.schedule(
            name="a", callback=lambda: None, trigger=OneShotTrigger(run_at=NOW + timedelta(seconds=1)), now=NOW)

        self.scheduler.tick(now=NOW + timedelta(seconds=1))

        started = self._events_of(EventType.TASK_STARTED)
        completed = self._events_of(EventType.TASK_COMPLETED)
        self.assertEqual(len(started), 1)
        self.assertEqual(len(completed), 1)
        self.assertEqual(started[0].payload["task_id"], task.id)

    def test_tick_publishes_scheduler_tick_event_every_call_even_with_nothing_due(self):
        self.scheduler.tick(now=NOW)

        ticks = self._events_of(EventType.SCHEDULER_TICK)
        self.assertEqual(len(ticks), 1)
        self.assertEqual(ticks[0].payload["executed"], 0)

    def test_scheduler_tick_payload_reports_executed_count(self):
        self.scheduler.schedule(name="a", callback=lambda: None, trigger=OneShotTrigger(run_at=NOW + timedelta(seconds=1)), now=NOW)
        self.scheduler.schedule(name="b", callback=lambda: None, trigger=OneShotTrigger(run_at=NOW + timedelta(seconds=1)), now=NOW)

        self.scheduler.tick(now=NOW + timedelta(seconds=1))

        ticks = self._events_of(EventType.SCHEDULER_TICK)
        self.assertEqual(ticks[-1].payload["executed"], 2)


# -- callback failures ----------------------------------------------------


class CallbackFailureTests(SchedulerTestCase):
    def test_failing_callback_does_not_raise_out_of_tick(self):
        def boom():
            raise ValueError("kaboom")

        self.scheduler.schedule(name="a", callback=boom, trigger=OneShotTrigger(run_at=NOW + timedelta(seconds=1)), now=NOW)

        executed = self.scheduler.tick(now=NOW + timedelta(seconds=1))

        self.assertEqual(executed, 1)  # counted as "processed", not "succeeded"

    def test_failing_callback_publishes_task_failed_with_error_details(self):
        def boom():
            raise ValueError("kaboom")

        task = self.scheduler.schedule(name="a", callback=boom, trigger=OneShotTrigger(run_at=NOW + timedelta(seconds=1)), now=NOW)

        self.scheduler.tick(now=NOW + timedelta(seconds=1))

        failed = self._events_of(EventType.TASK_FAILED)
        self.assertEqual(len(failed), 1)
        self.assertEqual(failed[0].payload["task_id"], task.id)
        self.assertEqual(failed[0].payload["error_type"], "ValueError")
        self.assertIn("kaboom", failed[0].payload["error"])

    def test_failing_callback_does_not_publish_task_completed(self):
        def boom():
            raise ValueError("kaboom")

        self.scheduler.schedule(name="a", callback=boom, trigger=OneShotTrigger(run_at=NOW + timedelta(seconds=1)), now=NOW)

        self.scheduler.tick(now=NOW + timedelta(seconds=1))

        self.assertEqual(self._events_of(EventType.TASK_COMPLETED), [])

    def test_recurring_task_is_still_rescheduled_after_failure(self):
        def boom():
            raise ValueError("kaboom")

        task = self.scheduler.schedule(
            name="a", callback=boom, trigger=IntervalTrigger(interval_seconds=10), now=NOW)

        self.scheduler.tick(now=NOW + timedelta(seconds=10))

        self.assertIsNotNone(self.scheduler.get_task(task.id).next_run)

    def test_one_task_failure_does_not_prevent_other_due_tasks_from_running(self):
        calls = []

        def boom():
            raise ValueError("kaboom")

        self.scheduler.schedule(name="failing", callback=boom, trigger=OneShotTrigger(run_at=NOW + timedelta(seconds=1)), now=NOW)
        self.scheduler.schedule(
            name="ok", callback=lambda: calls.append("ok"), trigger=OneShotTrigger(run_at=NOW + timedelta(seconds=1)), now=NOW)

        executed = self.scheduler.tick(now=NOW + timedelta(seconds=1))

        self.assertEqual(executed, 2)
        self.assertEqual(calls, ["ok"])


# -- multiple simultaneous tasks / ordering --------------------------------


class MultipleSimultaneousTasksTests(SchedulerTestCase):
    def test_multiple_due_tasks_all_execute_in_one_tick(self):
        calls = []
        for name in ("a", "b", "c"):
            self.scheduler.schedule(
                name=name, callback=lambda name=name: calls.append(name), trigger=OneShotTrigger(run_at=NOW + timedelta(seconds=1)), now=NOW)

        executed = self.scheduler.tick(now=NOW + timedelta(seconds=1))

        self.assertEqual(executed, 3)
        self.assertEqual(set(calls), {"a", "b", "c"})

    def test_higher_priority_tasks_execute_before_lower_priority_ones(self):
        order = []
        self.scheduler.schedule(
            name="low",
            callback=lambda: order.append("low"),
            trigger=OneShotTrigger(run_at=NOW + timedelta(seconds=1)),
            priority=TaskPriority.LOW, now=NOW,)
        self.scheduler.schedule(
            name="critical",
            callback=lambda: order.append("critical"),
            trigger=OneShotTrigger(run_at=NOW + timedelta(seconds=1)),
            priority=TaskPriority.CRITICAL, now=NOW,)
        self.scheduler.schedule(
            name="normal",
            callback=lambda: order.append("normal"),
            trigger=OneShotTrigger(run_at=NOW + timedelta(seconds=1)),
            priority=TaskPriority.NORMAL, now=NOW,)

        self.scheduler.tick(now=NOW + timedelta(seconds=1))

        self.assertEqual(order, ["critical", "normal", "low"])

    def test_same_priority_ties_broken_by_earliest_next_run(self):
        order = []
        self.scheduler.schedule(
            name="later",
            callback=lambda: order.append("later"),
            trigger=OneShotTrigger(run_at=NOW + timedelta(seconds=5)), now=NOW,)
        self.scheduler.schedule(
            name="earlier",
            callback=lambda: order.append("earlier"),
            trigger=OneShotTrigger(run_at=NOW + timedelta(seconds=1)), now=NOW,)

        self.scheduler.tick(now=NOW + timedelta(seconds=10))

        self.assertEqual(order, ["earlier", "later"])

    def test_callback_that_cancels_its_own_task_does_not_raise(self):
        # Exercises Scheduler._finish's guard for a task that no
        # longer exists by the time execution completes (e.g.
        # cancelled by its own callback, or by another caller between
        # being selected as due and finishing).
        task_id = "self-cancelling"

        def cancel_self():
            self.scheduler.cancel(task_id)

        self.scheduler.schedule(
            name="a",
            callback=cancel_self,
            trigger=OneShotTrigger(run_at=NOW + timedelta(seconds=1)),
            task_id=task_id,
            now=NOW,
        )

        executed = self.scheduler.tick(now=NOW + timedelta(seconds=1))

        self.assertEqual(executed, 1)
        with self.assertRaises(TaskNotFound):
            self.scheduler.get_task(task_id)

    def test_only_due_tasks_run_others_remain_pending(self):
        calls = []
        self.scheduler.schedule(
            name="due", callback=lambda: calls.append("due"), trigger=OneShotTrigger(run_at=NOW + timedelta(seconds=1)), now=NOW)
        not_due = self.scheduler.schedule(
            name="not_due",
            callback=lambda: calls.append("not_due"),
            trigger=OneShotTrigger(run_at=NOW + timedelta(hours=1)), now=NOW,)

        self.scheduler.tick(now=NOW + timedelta(seconds=1))

        self.assertEqual(calls, ["due"])
        self.assertIsNone(self.scheduler.get_task(not_due.id).last_run)


# -- lookup / listing -------------------------------------------------------


class LookupTests(SchedulerTestCase):
    def test_get_task_returns_scheduled_task(self):
        task = self.scheduler.schedule(
            name="a", callback=lambda: None, trigger=OneShotTrigger(run_at=NOW + timedelta(seconds=1)), now=NOW)

        self.assertEqual(self.scheduler.get_task(task.id), task)

    def test_get_task_missing_raises_task_not_found(self):
        with self.assertRaises(TaskNotFound):
            self.scheduler.get_task("missing")

    def test_list_tasks_empty_initially(self):
        self.assertEqual(self.scheduler.list_tasks(), ())

    def test_list_tasks_returns_all_scheduled_tasks(self):
        self.scheduler.schedule(name="a", callback=lambda: None, trigger=OneShotTrigger(run_at=NOW + timedelta(seconds=1)), now=NOW)
        self.scheduler.schedule(name="b", callback=lambda: None, trigger=OneShotTrigger(run_at=NOW + timedelta(seconds=1)), now=NOW)

        self.assertEqual(len(self.scheduler.list_tasks()), 2)

    def test_list_tasks_excludes_cancelled_tasks(self):
        task = self.scheduler.schedule(
            name="a", callback=lambda: None, trigger=OneShotTrigger(run_at=NOW + timedelta(seconds=1)), now=NOW)
        self.scheduler.cancel(task.id)

        self.assertEqual(self.scheduler.list_tasks(), ())

    def test_list_tasks_includes_paused_tasks(self):
        task = self.scheduler.schedule(
            name="a", callback=lambda: None, trigger=OneShotTrigger(run_at=NOW + timedelta(seconds=1)), now=NOW)
        self.scheduler.pause(task.id)

        self.assertEqual(len(self.scheduler.list_tasks()), 1)


if __name__ == "__main__":
    unittest.main()
