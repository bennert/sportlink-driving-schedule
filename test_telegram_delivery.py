import unittest
from unittest.mock import Mock, patch

from send_telegram_announcements import format_announcement, send_telegram_message


class TelegramDeliveryTests(unittest.TestCase):
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


if __name__ == '__main__':
    unittest.main()