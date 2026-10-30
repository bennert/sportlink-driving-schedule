"""Tests for environment-based team and delivery configuration validation."""

import unittest

from configuration_validation import validate_configuration


VALID_CONFIGURATION = {
    'MAPS_API_KEY': 'maps-secret-value',
    'SPORTLINK_TOKEN_LIST': 'EHV HS1:sportlink-secret',
    'SPORTLINK_TEAM_LIST': 'EHV HS1:Club Hall:60:0.23:coach@example.com',
    'EMAIL_USERNAME': 'sender@example.com',
    'EMAIL_PASSWORD': 'email-secret',
    'TELEGRAM_BOT_TOKEN': 'telegram-secret',
    'TELEGRAM_CHAT_LIST': 'EHV HS1:-1001',
}


class ConfigurationValidationTests(unittest.TestCase):
    """Verify environment and team delivery settings are validated."""

    def test_accepts_valid_configuration(self):
        """Accept a complete and valid team configuration."""
        self.assertEqual([], validate_configuration(VALID_CONFIGURATION, True, True))

    def test_reports_missing_settings_and_invalid_team_values(self):
        """Report missing required settings and invalid team values."""
        configuration = {
            'MAPS_API_KEY': '',
            'SPORTLINK_TOKEN_LIST': 'EHV HS1:sportlink-secret',
            'SPORTLINK_TEAM_LIST': 'EHV HS1:Club Hall:soon:-1:coach@example.com',
        }

        errors = validate_configuration(configuration)

        self.assertTrue(any('MAPS_API_KEY is required' in error for error in errors))
        self.assertTrue(any('numeric WARMUP_MINUTES and COST_PER_KM' in error for error in errors))

    def test_reports_invalid_telegram_configuration_without_echoing_secrets(self):
        """Reject invalid Telegram settings without exposing secrets."""
        configuration = dict(VALID_CONFIGURATION)
        configuration['TELEGRAM_CHAT_LIST'] = 'EHV HS1:not-a-chat-id'

        errors = validate_configuration(configuration, require_telegram=True)

        self.assertTrue(any('TELEGRAM_CHAT_LIST must contain' in error for error in errors))
        self.assertNotIn('telegram-secret', '\n'.join(errors))
        self.assertNotIn('sportlink-secret', '\n'.join(errors))
        self.assertNotIn('email-secret', '\n'.join(errors))

    def test_requires_telegram_settings_for_scheduled_announcements(self):
        """Require Telegram settings when announcements are scheduled."""
        configuration = {
            key: value for key, value in VALID_CONFIGURATION.items()
            if not key.startswith('TELEGRAM_')
        }

        errors = validate_configuration(configuration, require_telegram=True)

        self.assertTrue(any('TELEGRAM_BOT_TOKEN is required' in error for error in errors))
        self.assertTrue(any('TELEGRAM_CHAT_LIST is required' in error for error in errors))

    def test_reports_missing_team_tokens_and_destinations(self):
        """Report missing team tokens and Telegram destinations."""
        configuration = dict(VALID_CONFIGURATION)
        configuration['SPORTLINK_TOKEN_LIST'] = ''
        configuration['TELEGRAM_CHAT_LIST'] = 'EHV HS2:-2002'

        errors = validate_configuration(configuration, require_telegram=True)

        self.assertTrue(
            any('SPORTLINK_TOKEN_LIST is required' in error for error in errors))
        self.assertTrue(
            any('has no token configured for team EHV HS1' in error for error in errors))
        self.assertTrue(
            any('has no destination configured for team EHV HS1' in error for error in errors))
        self.assertTrue(
            any('references unknown team EHV HS2' in error for error in errors))


if __name__ == '__main__':
    unittest.main()
