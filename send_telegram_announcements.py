import json
import os
import re
import sys

import requests
from dotenv import load_dotenv

from telegram_config import get_team_chat_ids, parse_telegram_chat_list

load_dotenv()

LOCATION_LINK_PATTERN = re.compile(r'^\[(.*)\]\((.*)\)$')


def format_announcement(team_id, matches):
    sections = []
    for match in matches:
        location = match[6]
        location_link = LOCATION_LINK_PATTERN.match(location)
        if location_link:
            location = f'{location_link.group(1)}\nGoogle Maps: {location_link.group(2)}'
        sections.append(
            f'{match[2]}\n'
            f'Datum: {match[0]}\n'
            f'Aanvang: {match[4]}\n'
            f'Verzamelen: {match[3]}\n'
            f'Locatie: {location}\n'
            f'Reistijd: {match[9]} min | Afstand: {match[8]} km | Kosten: {match[7]}'
        )
    return f'Wedstrijden {team_id} (komende 7 dagen):\n\n' + '\n\n'.join(sections)


def send_telegram_message(bot_token, chat_id, text):
    url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
    try:
        response = requests.post(url, json={'chat_id': chat_id, 'text': text}, timeout=10)
    except requests.RequestException as error:
        raise RuntimeError('Telegram Bot API request failed') from error

    if response.status_code >= 400:
        raise RuntimeError(f'Telegram Bot API returned HTTP {response.status_code}')
    try:
        result = response.json()
    except ValueError as error:
        raise RuntimeError('Telegram Bot API returned invalid JSON') from error
    if not isinstance(result, dict) or not result.get('ok'):
        description = result.get('description', 'unknown error') if isinstance(result, dict) else 'unknown response'
        raise RuntimeError(f'Telegram Bot API rejected the message: {description}')


def main():
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        print('ERROR: TELEGRAM_BOT_TOKEN not set')
        return 1

    announcements_path = os.path.join('docs', 'telegram_announcements.json')
    try:
        destinations = parse_telegram_chat_list(os.getenv('TELEGRAM_CHAT_LIST'))
        with open(announcements_path, 'r', encoding='utf-8') as file:
            announcements = json.load(file)
    except (OSError, ValueError) as error:
        print(f'ERROR: {error}')
        return 1

    failed = False
    sent_count = 0
    for announcement in announcements:
        team_id = announcement['team_id']
        matches = announcement['matches']
        if not matches:
            continue
        try:
            chat_ids = get_team_chat_ids(destinations, team_id)
        except ValueError as error:
            print(f'ERROR for {team_id}: {error}')
            failed = True
            continue

        message = format_announcement(team_id, matches)
        for chat_id in chat_ids:
            try:
                send_telegram_message(bot_token, chat_id, message)
            except RuntimeError as error:
                print(f'Failed Telegram delivery for {team_id}: {error}')
                failed = True
            else:
                sent_count += 1

    if failed:
        return 1
    print(f'Sent {sent_count} Telegram announcement(s)')
    return 0


if __name__ == '__main__':
    sys.exit(main())