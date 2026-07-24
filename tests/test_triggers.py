"""Unit tests for argus.scheduler.triggers."""

import unittest
from datetime import datetime, timedelta, timezone

from argus.scheduler import DailyTrigger, IntervalTrigger, InvalidTrigger, OneShotTrigger


class OneShotTriggerTests(unittest.TestCase):
    def test_returns_run_at_when_still_in_the_future(self):
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        run_at = now + timedelta(hours=1)
        trigger = OneShotTrigger(run_at=run_at)

        self.assertEqual(trigger.next_fire_time(after=now), run_at)

    def test_returns_none_once_after_reaches_run_at(self):
        run_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
        trigger = OneShotTrigger(run_at=run_at)

        self.assertIsNone(trigger.next_fire_time(after=run_at))

    def test_returns_none_once_after_passes_run_at(self):
        run_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
        trigger = OneShotTrigger(run_at=run_at)

        self.assertIsNone(trigger.next_fire_time(after=run_at + timedelta(seconds=1)))

    def test_returns_none_when_run_at_is_already_in_the_past_at_first_use(self):
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        trigger = OneShotTrigger(run_at=now - timedelta(hours=1))

        self.assertIsNone(trigger.next_fire_time(after=now))


class IntervalTriggerTests(unittest.TestCase):
    def test_next_fire_time_is_after_plus_interval_with_no_start_at(self):
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        trigger = IntervalTrigger(interval_seconds=30)

        self.assertEqual(trigger.next_fire_time(after=now), now + timedelta(seconds=30))

    def test_repeated_calls_advance_by_interval_each_time(self):
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        trigger = IntervalTrigger(interval_seconds=10)

        first = trigger.next_fire_time(after=now)
        second = trigger.next_fire_time(after=first)

        self.assertEqual(second, first + timedelta(seconds=10))

    def test_start_at_in_the_future_delays_first_fire(self):
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        start_at = now + timedelta(hours=2)
        trigger = IntervalTrigger(interval_seconds=30, start_at=start_at)

        self.assertEqual(trigger.next_fire_time(after=now), start_at)

    def test_start_at_in_the_past_falls_back_to_after_plus_interval(self):
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        start_at = now - timedelta(hours=2)
        trigger = IntervalTrigger(interval_seconds=30, start_at=start_at)

        self.assertEqual(trigger.next_fire_time(after=now), now + timedelta(seconds=30))

    def test_zero_interval_raises_invalid_trigger(self):
        with self.assertRaises(InvalidTrigger):
            IntervalTrigger(interval_seconds=0)

    def test_negative_interval_raises_invalid_trigger(self):
        with self.assertRaises(InvalidTrigger):
            IntervalTrigger(interval_seconds=-5)


class DailyTriggerTests(unittest.TestCase):
    def test_returns_todays_occurrence_when_still_ahead(self):
        after = datetime(2026, 1, 1, 8, 0, 0, tzinfo=timezone.utc)
        trigger = DailyTrigger(hour=12, minute=30)

        expected = datetime(2026, 1, 1, 12, 30, 0, tzinfo=timezone.utc)
        self.assertEqual(trigger.next_fire_time(after=after), expected)

    def test_returns_tomorrows_occurrence_when_todays_has_passed(self):
        after = datetime(2026, 1, 1, 14, 0, 0, tzinfo=timezone.utc)
        trigger = DailyTrigger(hour=12, minute=30)

        expected = datetime(2026, 1, 2, 12, 30, 0, tzinfo=timezone.utc)
        self.assertEqual(trigger.next_fire_time(after=after), expected)

    def test_returns_tomorrow_when_exactly_at_the_boundary(self):
        after = datetime(2026, 1, 1, 12, 30, 0, tzinfo=timezone.utc)
        trigger = DailyTrigger(hour=12, minute=30)

        expected = datetime(2026, 1, 2, 12, 30, 0, tzinfo=timezone.utc)
        self.assertEqual(trigger.next_fire_time(after=after), expected)

    def test_default_minute_and_second_are_zero(self):
        after = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        trigger = DailyTrigger(hour=6)

        expected = datetime(2026, 1, 1, 6, 0, 0, tzinfo=timezone.utc)
        self.assertEqual(trigger.next_fire_time(after=after), expected)

    def test_hour_out_of_range_raises_invalid_trigger(self):
        with self.assertRaises(InvalidTrigger):
            DailyTrigger(hour=24)

    def test_negative_hour_raises_invalid_trigger(self):
        with self.assertRaises(InvalidTrigger):
            DailyTrigger(hour=-1)

    def test_minute_out_of_range_raises_invalid_trigger(self):
        with self.assertRaises(InvalidTrigger):
            DailyTrigger(hour=12, minute=60)

    def test_second_out_of_range_raises_invalid_trigger(self):
        with self.assertRaises(InvalidTrigger):
            DailyTrigger(hour=12, second=60)


if __name__ == "__main__":
    unittest.main()
