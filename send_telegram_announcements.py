"""Format and deliver scheduled match announcements through Telegram."""

import json
import os
import re
import sys
from datetime import date

import requests
from dotenv import load_dotenv

from telegram_config import get_team_chat_ids, parse_telegram_chat_list

load_dotenv()

ANNOUNCEMENTS_PATH = os.path.join('docs', 'telegram_announcements.json')
LOCATION_LINK_PATTERN = re.compile(r'^\[(.*)\]\((.*)\)$')
DUTCH_WEEKDAYS = (
    'maandag', 'dinsdag', 'woensdag', 'donderdag', 'vrijdag', 'zaterdag', 'zondag'
)
DUTCH_MONTHS = (
    'januari', 'februari', 'maart', 'april', 'mei', 'juni',
    'juli', 'augustus', 'september', 'oktober', 'november', 'december'
)


def format_match_date(date_value):
    """Format an ISO date using Dutch weekday and month names."""
    match_date = date.fromisoformat(date_value)
    return (
        f'{DUTCH_WEEKDAYS[match_date.weekday()]} {match_date.day} '
        f'{DUTCH_MONTHS[match_date.month - 1]} {match_date.year}'
    )


def format_announcement(team_id, matches):
    """Format a team's upcoming matches as a Telegram message."""
    heading = f'Wedstrijden {team_id} (komende 7 dagen):'
    if not matches:
        return f'{heading}\n\nGeen wedstrijden gepland.'

    sections = []
    for match in matches:
        location = match[6]
        location_link = LOCATION_LINK_PATTERN.match(location)
        if location_link:
            location = f'{location_link.group(1)}\nGoogle Maps: {location_link.group(2)}'
        sections.append(
            f'{match[2]}\n'
            f'Datum: {format_match_date(match[0])}\n'
            f'Aanvang: {match[4]}\n'
            f'Verzamelen: {match[3]}\n'
            f'Locatie: {location}\n'
            f'Reiskosten: {match[7]}'
        )
    return f'{heading}\n\n' + '\n\n'.join(sections)


def _markdown_cell(value):
    """Escape Markdown characters and line breaks in a table cell."""
    return str(value) \
        .replace('\\', '\\\\') \
        .replace('|', '\\|') \
        .replace('\r', ' ') \
        .replace('\n', ' ')


def format_delivery_summary(results):
    """Format per-destination Telegram delivery results as a Markdown table."""
    lines = [
        '## Telegram delivery results',
        '',
        '| Team | Destination | Result | Details |',
        '| --- | --- | --- | --- |',
    ]
    if not results:
        lines.append('| - | - | Not sent | No team notifications were processed. |')
    for result in results:
        lines.append(
            '| ' + ' | '.join(_markdown_cell(result[field]) for field in (
                'team_id', 'destination', 'status', 'details'
            )) + ' |'
        )
    return '\n'.join(lines)


def send_telegram_message(bot_token, chat_id, text):
    """Send a message to a Telegram chat or raise on delivery failure."""
    url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
    try:
        response = requests.post(url, json={'chat_id': chat_id, 'text': text}, timeout=10)
    except requests.RequestException as error:
        raise RuntimeError('Telegram Bot API request failed') from error

    try:
        result = response.json()
    except ValueError:
        result = None
    if response.status_code >= 400:
        description = result.get('description') if isinstance(result, dict) else None
        detail = f': {description}' if description else ''
        raise RuntimeError(f'Telegram Bot API returned HTTP {response.status_code}{detail}')
    if not isinstance(result, dict) or not result.get('ok'):
        description = result.get(
            'description', 'unknown error') if isinstance(result, dict) else 'unknown response'
        raise RuntimeError(f'Telegram Bot API rejected the message: {description}')


def main():
    """Load announcements, deliver them, and report delivery outcomes."""
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        print('ERROR: TELEGRAM_BOT_TOKEN not set')
        return 1

    try:
        destinations = parse_telegram_chat_list(os.getenv('TELEGRAM_CHAT_LIST'))
        with open(ANNOUNCEMENTS_PATH, 'r', encoding='utf-8') as file:
            announcements = json.load(file)
    except (OSError, ValueError) as error:
        print(f'ERROR: {error}')
        return 1

    failed = False
    sent_count = 0
    delivery_results = []
    for announcement in announcements:
        team_id = announcement['team_id']
        matches = announcement['matches']
        try:
            chat_ids = get_team_chat_ids(destinations, team_id)
        except ValueError as error:
            print(f'ERROR for {team_id}: {error}')
            delivery_results.append({
                'team_id': team_id,
                'destination': 'not configured',
                'status': 'Failed',
                'details': str(error),
            })
            failed = True
            continue

        message = format_announcement(team_id, matches)
        for chat_id in chat_ids:
            try:
                send_telegram_message(bot_token, chat_id, message)
            except RuntimeError as error:
                safe_error = str(error).replace(bot_token, '[REDACTED]')
                print(f'Failed Telegram delivery for {team_id}: {safe_error}')
                delivery_results.append({
                    'team_id': team_id,
                    'destination': chat_id,
                    'status': 'Failed',
                    'details': safe_error,
                })
                failed = True
            else:
                sent_count += 1
                delivery_results.append({
                    'team_id': team_id,
                    'destination': chat_id,
                    'status': 'Sent',
                    'details': 'Telegram accepted the message.',
                })

    summary = format_delivery_summary(delivery_results)
    print(summary)
    summary_path = os.getenv('GITHUB_STEP_SUMMARY')
    if summary_path:
        try:
            with open(summary_path, 'a', encoding='utf-8') as summary_file:
                summary_file.write(summary + '\n')
        except OSError:
            print('ERROR: Could not write the GitHub Actions delivery summary.')
            failed = True

    if failed:
        return 1
    print(f'Sent {sent_count} Telegram announcement(s)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
