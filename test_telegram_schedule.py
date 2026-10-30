"""Tests for selecting matches in the upcoming seven-day window."""

import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

from telegram_schedule import select_matches_in_next_seven_days


class TelegramScheduleTests(unittest.TestCase):
    """Verify date boundaries when selecting upcoming matches."""

    def test_selects_matches_from_now_until_but_not_at_seven_day_deadline(self):
        """Include matches from now but exclude the exact seven-day deadline."""
        now = datetime(2026, 10, 28, 12, 0, tzinfo=ZoneInfo('Europe/Amsterdam'))
        matches = [
            ['2026-10-28', '', 'Started', '', '11:59', '', '', '', '', ''],
            ['2026-10-28', '', 'At start', '', '12:00', '', '', '', '', ''],
            ['2026-11-04', '', 'Before deadline', '', '11:59', '', '', '', '', ''],
            ['2026-11-04', '', 'At deadline', '', '12:00', '', '', '', '', ''],
        ]

        selected = select_matches_in_next_seven_days(matches, now)

        self.assertEqual(['At start', 'Before deadline'], [match[2] for match in selected])

    def test_returns_no_matches_when_window_is_empty(self):
        """Return an empty selection when no matches fall in the time window."""
        now = datetime(2026, 10, 28, 12, 0, tzinfo=ZoneInfo('Europe/Amsterdam'))

        self.assertEqual([], select_matches_in_next_seven_days([], now))


if __name__ == '__main__':
    unittest.main()