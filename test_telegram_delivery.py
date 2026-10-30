"""Tests for Telegram announcement formatting and delivery outcomes."""

import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import Mock, call, patch

from send_telegram_announcements import (
    format_announcement,
    format_delivery_summary,
    main,
    send_telegram_message,
)


class TelegramDeliveryTests(unittest.TestCase):
    """Verify Telegram announcement formatting and delivery handling."""

    def test_format_empty_announcement_names_team_and_period(self):
        """Name the team and covered period when no matches are scheduled."""
        message = format_announcement('EHV HS1', [])

        self.assertEqual(
            'Wedstrijden EHV HS1 (komende 7 dagen):\n\nGeen wedstrijden gepland.',
            message,
        )

    def test_send_empty_announcement_to_every_team_destination(self):
        """Send the no-matches announcement to every configured destination."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            announcements_path = Path(temporary_directory) / 'announcements.json'
            announcements_path.write_text(
                json.dumps([{'team_id': 'EHV HS1', 'matches': []}]), encoding='utf-8'
            )
            output = io.StringIO()
            with patch.dict(os.environ, {
                'TELEGRAM_BOT_TOKEN': 'test-token',
                'TELEGRAM_CHAT_LIST': 'EHV HS1:-1001;-1002',
            }, clear=True), patch('send_telegram_announcements.ANNOUNCEMENTS_PATH', str(announcements_path)), \
                    patch('send_telegram_announcements.send_telegram_message') as send_message, \
                    redirect_stdout(output):
                result = main()

        self.assertEqual(0, result)
        self.assertEqual(2, send_message.call_count)
        message = format_announcement('EHV HS1', [])
        send_message.assert_has_calls([
            call('test-token', '-1001', message),
            call('test-token', '-1002', message),
        ])
        self.assertIn('Sent 2 Telegram announcement(s)', output.getvalue())

    def test_summarize_success_and_failure_per_destination(self):
        """Summarize successful and failed Telegram destinations separately."""
        summary = format_delivery_summary([
            {
                'team_id': 'EHV HS1', 'destination': '-1001', 'status': 'Sent',
                'details': 'Telegram accepted the message.',
            },
            {
                'team_id': 'EHV HS1', 'destination': '-1002', 'status': 'Failed',
                'details': 'Telegram returned HTTP 400: chat not found.',
            },
        ])

        self.assertIn('| EHV HS1 | -1001 | Sent |', summary)
        self.assertIn('| EHV HS1 | -1002 | Failed | Telegram returned HTTP 400: chat not found. |', summary)

    def test_partial_delivery_failure_is_summarized_and_fails_run(self):
        """Fail the run and summarize results when only some sends succeed."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            announcements_path = Path(temporary_directory) / 'announcements.json'
            summary_path = Path(temporary_directory) / 'summary.md'
            announcements_path.write_text(
                json.dumps([{'team_id': 'EHV HS1', 'matches': []}]), encoding='utf-8'
            )
            output = io.StringIO()

            def send_message(bot_token, chat_id, _message):
                """Simulate a send failure for one destination."""
                if chat_id == '-1002':
                    raise RuntimeError(f'Telegram error for {bot_token}: chat not found')

            with patch.dict(os.environ, {
                'TELEGRAM_BOT_TOKEN': 'top-secret-token',
                'TELEGRAM_CHAT_LIST': 'EHV HS1:-1001;-1002',
                'GITHUB_STEP_SUMMARY': str(summary_path),
            }, clear=True), patch('send_telegram_announcements.ANNOUNCEMENTS_PATH', str(announcements_path)), \
                    patch('send_telegram_announcements.send_telegram_message', side_effect=send_message), \
                    redirect_stdout(output):
                result = main()

            summary = summary_path.read_text(encoding='utf-8')
            self.assertEqual(1, result)
            self.assertIn('| EHV HS1 | -1001 | Sent |', summary)
            self.assertIn('| EHV HS1 | -1002 | Failed |', summary)
            self.assertIn('[REDACTED]: chat not found', summary)
            self.assertNotIn('top-secret-token', summary)
            self.assertIn('## Telegram delivery results', output.getvalue())

    def test_format_announcement_includes_match_and_travel_details(self):
        """Include match, location, and travel details in announcements."""
        match = [
            '2026-11-01', 'Sunday', 'Opponent-Team', '10:00', '11:00', '13:00',
            '[Sports Hall](https://maps.example/match)', '€ 4.20'
        ]

        message = format_announcement('EHV DS1', [match])

        for detail in ('EHV DS1', 'Opponent-Team', 'zondag 1 november 2026',
                   'Aanvang: 11:00', 'Verzamelen: 10:00',
                       'Sports Hall', 'https://maps.example/match', '€ 4.20'):
            with self.subTest(detail=detail):
                self.assertIn(detail, message)
        self.assertNotIn('Reistijd:', message)
        self.assertNotIn('Afstand:', message)

    def test_format_announcement_separates_each_match(self):
        """Separate consecutive matches into distinct message sections."""
        first_match = [
            '2026-11-01', 'Sunday', 'Opponent-One', '10:00', '11:00', '13:00',
            '[Sports Hall](https://maps.example/one)', '€ 4.20'
        ]
        second_match = [
            '2026-11-02', 'Monday', 'Opponent-Two', '16:00', '17:00', '19:00',
            '[Other Hall](https://maps.example/two)', '€ 2.10'
        ]

        message = format_announcement('EHV DS1', [first_match, second_match])

        self.assertIn('€ 4.20\n\nOpponent-Two', message)
        self.assertIn('maandag 2 november 2026', message)

    @patch('send_telegram_announcements.requests.post')
    def test_send_posts_to_telegram_bot_api(self, post):
        """Post the expected message payload to the Telegram Bot API."""
        response = Mock(status_code=200)
        response.json.return_value = {'ok': True}
        post.return_value = response

        send_telegram_message('secret-token', '-1001', 'Weekly match')

        post.assert_called_once_with(
            'https://api.telegram.org/botsecret-token/sendMessage',
            json={'chat_id': '-1001', 'text': 'Weekly match'},
            timeout=10,
        )

    @patch('send_telegram_announcements.requests.post')
    def test_report_telegram_api_rejection(self, post):
        """Report an API rejection instead of accepting a failed send."""
        response = Mock(status_code=200)
        response.json.return_value = {'ok': False, 'description': 'Forbidden'}
        post.return_value = response

        with self.assertRaisesRegex(RuntimeError, 'Forbidden'):
            send_telegram_message('secret-token', '-1001', 'Weekly match')

    @patch('send_telegram_announcements.requests.post')
    def test_include_api_description_for_http_400(self, post):
        """Include Telegram's error description for HTTP 400 responses."""
        response = Mock(status_code=400)
        response.json.return_value = {
            'ok': False,
            'description': 'Bad Request: chat not found',
        }
        post.return_value = response

        with self.assertRaisesRegex(RuntimeError, 'HTTP 400: Bad Request: chat not found'):
            send_telegram_message('secret-token', '-1001', 'Weekly match')


if __name__ == '__main__':
    unittest.main()