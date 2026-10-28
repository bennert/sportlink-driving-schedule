import unittest

from telegram_config import get_team_chat_ids, parse_telegram_chat_list


class TelegramConfigTests(unittest.TestCase):
    def test_parse_multiple_chat_destinations_by_team(self):
        destinations = parse_telegram_chat_list('EHV DS1:-1001;1002,EHV HS1:-2001')

        self.assertEqual({'EHV DS1': ('-1001', '1002'), 'EHV HS1': ('-2001',)}, destinations)

    def test_reject_invalid_or_duplicate_destinations(self):
        for value in ('missing-separator', 'EHV DS1:', 'EHV DS1:not-a-number', 'EHV DS1:1,EHV DS1:2', 'EHV DS1:1;1'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_telegram_chat_list(value)

    def test_missing_team_destination_is_reported(self):
        with self.assertRaisesRegex(ValueError, 'No Telegram destination configured'):
            get_team_chat_ids({}, 'EHV DS1')


if __name__ == '__main__':
    unittest.main()