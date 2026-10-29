import io
import json
import os
import unittest
from contextlib import redirect_stdout
from unittest.mock import Mock, call, mock_open, patch

from send_telegram_announcements import format_announcement, main, send_telegram_message


class TelegramDeliveryTests(unittest.TestCase):
    def test_format_empty_announcement_names_team_and_period(self):
        message = format_announcement('EHV HS1', [])

        self.assertEqual(
            'Wedstrijden EHV HS1 (komende 7 dagen):\n\nGeen wedstrijden gepland.',
            message,
        )

    def test_send_empty_announcement_to_every_team_destination(self):
        announcement_data = json.dumps([{'team_id': 'EHV HS1', 'matches': []}])
        output = io.StringIO()
        with patch.dict(os.environ, {
            'TELEGRAM_BOT_TOKEN': 'test-token',
            'TELEGRAM_CHAT_LIST': 'EHV HS1:-1001;-1002',
        }, clear=True), patch('builtins.open', mock_open(read_data=announcement_data)), \
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

    def test_format_announcement_includes_match_and_travel_details(self):
        match = [
            '2026-11-01', 'Sunday', 'Opponent-Team', '10:00', '11:00', '13:00',
            '[Sports Hall](https://maps.example/match)', '€ 4.20'
        ]

        message = format_announcement('EHV DS1', [match])

        for detail in ('EHV DS1', 'Opponent-Team', '2026-11-01', '11:00', '10:00',
                       'Sports Hall', 'https://maps.example/match', '€ 4.20'):
            with self.subTest(detail=detail):
                self.assertIn(detail, message)
        self.assertNotIn('Reistijd:', message)
        self.assertNotIn('Afstand:', message)

    @patch('send_telegram_announcements.requests.post')
    def test_send_posts_to_telegram_bot_api(self, post):
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
        response = Mock(status_code=200)
        response.json.return_value = {'ok': False, 'description': 'Forbidden'}
        post.return_value = response

        with self.assertRaisesRegex(RuntimeError, 'Forbidden'):
            send_telegram_message('secret-token', '-1001', 'Weekly match')

    @patch('send_telegram_announcements.requests.post')
    def test_include_api_description_for_http_400(self, post):
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