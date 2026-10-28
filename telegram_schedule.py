from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo


AMSTERDAM = ZoneInfo('Europe/Amsterdam')


def select_matches_in_next_seven_days(matches, now=None):
    now = now or datetime.now(AMSTERDAM)
    now = now.replace(tzinfo=AMSTERDAM) if now.tzinfo is None else now.astimezone(AMSTERDAM)
    deadline = now + timedelta(days=7)
    selected = []
    for match in matches:
        starts_at = datetime.combine(
            date.fromisoformat(match[0]), time.fromisoformat(match[4]), tzinfo=AMSTERDAM
        )
        if now <= starts_at < deadline:
            selected.append(match)
    return selected