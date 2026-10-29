import math
import os
import sys

from telegram_config import parse_telegram_chat_list


TEAM_CONFIGURATION_FORMAT = 'TEAM_ID:BASE_LOCATION:WARMUP_MINUTES:COST_PER_KM[:TEAM_EMAIL]'
TOKEN_CONFIGURATION_FORMAT = 'TEAM_ID:TOKEN'


def validate_configuration(environment, require_email=False, require_telegram=False):
    errors = []
    required_names = ('MAPS_API_KEY', 'SPORTLINK_TOKEN_LIST', 'SPORTLINK_TEAM_LIST')
    for name in required_names:
        if not (environment.get(name) or '').strip():
            errors.append(f'{name} is required.')

    tokens_by_team = {}
    raw_tokens = (environment.get('SPORTLINK_TOKEN_LIST') or '').strip()
    if raw_tokens:
        for entry in raw_tokens.split(','):
            team_id, separator, token = entry.partition(':')
            team_id = team_id.strip()
            if not separator or not team_id or not token.strip():
                errors.append(
                    f'SPORTLINK_TOKEN_LIST entries must use {TOKEN_CONFIGURATION_FORMAT}.'
                )
                continue
            if team_id in tokens_by_team:
                errors.append(f'SPORTLINK_TOKEN_LIST contains duplicate team {team_id}.')
                continue
            tokens_by_team[team_id] = token.strip()

    teams = {}
    raw_teams = (environment.get('SPORTLINK_TEAM_LIST') or '').strip()
    if raw_teams:
        for entry in raw_teams.split(','):
            fields = [field.strip() for field in entry.split(':')]
            team_id = fields[0] if fields else ''
            if len(fields) not in (4, 5) or not team_id or any(
                not field for field in fields[:4]
            ):
                errors.append(
                    f'SPORTLINK_TEAM_LIST entries must use {TEAM_CONFIGURATION_FORMAT}.'
                )
                continue
            if team_id in teams:
                errors.append(f'SPORTLINK_TEAM_LIST contains duplicate team {team_id}.')
                continue
            try:
                warmup_minutes = float(fields[2])
                cost_per_km = float(fields[3])
            except ValueError:
                errors.append(
                    f'Team {team_id} must have numeric WARMUP_MINUTES and COST_PER_KM values.'
                )
                continue
            if not math.isfinite(warmup_minutes) or warmup_minutes < 0:
                errors.append(f'Team {team_id} WARMUP_MINUTES must be a non-negative number.')
            if not math.isfinite(cost_per_km) or cost_per_km < 0:
                errors.append(f'Team {team_id} COST_PER_KM must be a non-negative number.')
            teams[team_id] = fields

    for team_id in teams:
        if team_id not in tokens_by_team:
            errors.append(f'SPORTLINK_TOKEN_LIST has no token configured for team {team_id}.')
    for team_id in tokens_by_team:
        if team_id not in teams:
            errors.append(f'SPORTLINK_TOKEN_LIST references unknown team {team_id}.')

    if require_email:
        for name in ('EMAIL_USERNAME', 'EMAIL_PASSWORD'):
            if not (environment.get(name) or '').strip():
                errors.append(f'{name} is required.')

    telegram_values = (
        environment.get('TELEGRAM_BOT_TOKEN'),
        environment.get('TELEGRAM_CHAT_LIST'),
    )
    telegram_configured = any((value or '').strip() for value in telegram_values)
    if require_telegram:
        for name, value in zip(('TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_LIST'), telegram_values):
            if not (value or '').strip():
                errors.append(f'{name} is required for scheduled Telegram announcements.')
    if require_telegram or telegram_configured:
        destinations = {}
        raw_destinations = environment.get('TELEGRAM_CHAT_LIST') or ''
        if raw_destinations.strip():
            try:
                destinations = parse_telegram_chat_list(raw_destinations)
            except ValueError:
                errors.append(
                    'TELEGRAM_CHAT_LIST must contain unique teams with numeric chat IDs '
                    'in TEAM_ID:CHAT_ID[;CHAT_ID] format.'
                )
        if destinations:
            for team_id in teams:
                if team_id not in destinations:
                    errors.append(f'TELEGRAM_CHAT_LIST has no destination configured for team {team_id}.')
            for team_id in destinations:
                if team_id not in teams:
                    errors.append(f'TELEGRAM_CHAT_LIST references unknown team {team_id}.')

    return errors


def main():
    errors = validate_configuration(
        os.environ,
        require_telegram=os.environ.get('GITHUB_EVENT_NAME') == 'schedule',
    )
    if errors:
        print('ERROR: Configuration validation failed:')
        for error in errors:
            print(f'- {error}')
        return 1
    print('Configuration is valid.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
