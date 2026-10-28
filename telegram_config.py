def parse_telegram_chat_list(value):
    destinations = {}
    entries = (entry.strip() for entry in (value or '').split(','))
    for entry in filter(None, entries):
        team_id, separator, raw_chat_ids = entry.partition(':')
        team_id = team_id.strip()
        chat_ids = [chat_id.strip() for chat_id in raw_chat_ids.split(';')]
        if not separator or not team_id or not all(chat_ids):
            raise ValueError(f'Invalid Telegram destination entry: {entry}')
        try:
            chat_ids = tuple(str(int(chat_id)) for chat_id in chat_ids)
        except ValueError as error:
            raise ValueError(f'Invalid Telegram chat ID for team {team_id}') from error
        if team_id in destinations or len(set(chat_ids)) != len(chat_ids):
            raise ValueError(f'Duplicate Telegram destination for team {team_id}')
        destinations[team_id] = chat_ids
    return destinations


def get_team_chat_ids(destinations, team_id):
    try:
        return destinations[team_id]
    except KeyError as error:
        raise ValueError(f'No Telegram destination configured for team {team_id}') from error