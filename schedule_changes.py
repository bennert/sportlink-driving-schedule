from collections import Counter
from datetime import datetime
import hashlib
from pathlib import Path
import re

from schedule_content import LOCATION_LINK_PATTERN, strip_travel_metrics


MATCH_FIELDS = ('date', 'weekday', 'description', 'collection_time', 'start_time', 'end_time', 'location')
WEEKDAYS = dict(zip(
    ('Maandag', 'Dinsdag', 'Woensdag', 'Donderdag', 'Vrijdag', 'Zaterdag', 'Zondag'),
    ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'),
))
SETTING_LABELS = {
    'Base location:': 'base_location', 'Basis locatie:': 'base_location',
    'Warming Up Time:': 'warming_up_time', 'Warming Up Tijd:': 'warming_up_time',
}
COMPARISON_NOTICES = {
    'legacy': {
        'nl': 'Wijzigingsoverzicht niet beschikbaar',
        'en': 'Change report unavailable',
    },
    'missing': {
        'nl': 'Geen vorige versie beschikbaar; wijzigingen konden niet worden bepaald',
        'en': 'No previous version available; changes could not be determined',
    },
    'unreadable': {
        'nl': 'Vorige versie onleesbaar; wijzigingen konden niet worden bepaald',
        'en': 'Previous version unreadable; changes could not be determined',
    },
}


def version_reference(filename, content):
    return {'filename': Path(filename).name,
            'digest': hashlib.sha256(content.encode('utf-8')).hexdigest()}


def build_change_report(team_id, previous_content, current_content, previous_name, current_name,
                        previous_ids=None, current_ids=None):
    current = parse_schedule(current_content, current_ids)
    report = {
        'schema_version': 1, 'team_id': team_id,
        'current': version_reference(current_name, current_content),
        'baseline': None, 'comparison': 'missing', 'entries': [], 'snapshot': current,
    }
    if previous_content is not None:
        report['baseline'] = version_reference(previous_name, previous_content)
        try:
            previous = parse_schedule(previous_content, previous_ids)
        except ValueError:
            report['comparison'] = 'unreadable'
        else:
            report['comparison'] = 'compared'
            report['entries'] = compare_schedules(previous, current)
    return report


def comparison_notice(report, language):
    if report['comparison'] != 'compared':
        return COMPARISON_NOTICES[report['comparison']][language]
    baseline = report['baseline']
    label = 'Vorige beschikbare versie' if language == 'nl' else 'Previous available version'
    return f"{label}: {baseline['filename']} ({baseline['digest']})"


def parse_schedule(content, match_ids=None):
    matches, settings, document = [], {}, []
    table_found = False
    columns = None
    for line in strip_travel_metrics(content).splitlines():
        line = line.strip()
        if not line or line in ('<!-- INFO_START -->', '<!-- INFO_END -->'):
            continue
        if line.startswith(('# Rijschema ', '# Driving schedule ', 'Cost per km:', 'Kosten per km:')):
            continue
        setting = next((label for label in SETTING_LABELS if line.startswith(label)), None)
        if setting:
            settings[SETTING_LABELS[setting]] = line[len(setting):].strip()
            continue
        logo = re.fullmatch(r'<!-- (CLUB_LOGO|TEAM_LOGO): (.+) -->', line)
        if logo:
            settings[logo.group(1).lower()] = logo.group(2)
            continue
        if line.startswith('|'):
            cells = [cell.strip() for cell in line.strip('|').split('|')]
            if cells[0] in ('Date', 'Datum'):
                if len(cells) not in (8, 10):
                    raise ValueError('Unsupported schedule table')
                table_found, columns = True, len(cells)
                continue
            if all(re.fullmatch(r':?-+:?', cell) for cell in cells[:7]):
                continue
            if not table_found or len(cells) != columns:
                raise ValueError('Invalid schedule row')
            datetime.strptime(cells[0], '%Y-%m-%d')
            for value in cells[3:6]:
                datetime.strptime(value, '%H:%M')
            match = dict(zip(MATCH_FIELDS, cells[:7]))
            match['weekday'] = WEEKDAYS.get(match['weekday'], match['weekday'])
            location = LOCATION_LINK_PATTERN.fullmatch(match['location'])
            if location:
                match['location'] = location.group(1)
            matches.append(match)
            continue
        document.append(line)
    if not table_found:
        raise ValueError('Schedule table missing')
    if match_ids is not None:
        if len(match_ids) != len(matches):
            raise ValueError('Match identifiers do not match schedule rows')
        for match, identifier in zip(matches, match_ids):
            if identifier:
                match['uid'] = str(identifier)
    return {'matches': matches, 'settings': settings, 'document': document, 'columns': columns}


def compare_schedules(previous, current):
    old_matches, new_matches = previous['matches'], current['matches']
    old_remaining, new_remaining = set(range(len(old_matches))), set(range(len(new_matches)))
    pairs = []
    for key in ('uid', 'legacy'):
        def identity(match, matching_key=key):
            return match.get('uid') if matching_key == 'uid' else (match['date'], match['description'])

        old_counts = Counter(identity(match) for match in old_matches)
        new_counts = Counter(identity(match) for match in new_matches)
        new_lookup = {identity(new_matches[index]): index for index in new_remaining}
        for old_index in sorted(old_remaining):
            old_match = old_matches[old_index]
            value = identity(old_match)
            if not value or old_counts[value] != 1 or new_counts[value] != 1:
                continue
            new_index = new_lookup[value]
            new_match = new_matches[new_index]
            if key == 'legacy' and old_match.get('uid') and new_match.get('uid'):
                continue
            pairs.append((old_match, new_match))
            old_remaining.remove(old_index)
            new_remaining.remove(new_index)
    for old_index in sorted(old_remaining.copy()):
        new_index = next((index for index in sorted(new_remaining)
                          if old_matches[old_index] == new_matches[index]), None)
        if new_index is not None:
            old_remaining.remove(old_index)
            new_remaining.remove(new_index)
    entries = []
    for old_match, new_match in pairs:
        for field in MATCH_FIELDS:
            if old_match[field] != new_match[field]:
                entries.append({
                    'kind': 'modified', 'field': field,
                    'old': old_match[field], 'new': new_match[field],
                    'date': new_match['date'], 'description': new_match['description'],
                })
    for kind, remaining, matches in (
        ('removed', old_remaining, old_matches), ('added', new_remaining, new_matches),
    ):
        for index in sorted(remaining):
            match = {field: matches[index][field] for field in MATCH_FIELDS}
            entries.append({'kind': kind, 'date': match['date'],
                            'description': match['description'], 'match': match})
    for field in sorted(previous['settings'].keys() | current['settings'].keys()):
        old_value, new_value = previous['settings'].get(field, ''), current['settings'].get(field, '')
        if old_value != new_value:
            entries.append({'kind': 'document' if field.endswith('_logo') else 'setting',
                            'field': field, 'old': old_value, 'new': new_value})
    for field in ('document', 'columns'):
        if previous[field] != current[field]:
            entries.append({'kind': 'document', 'field': field,
                            'old': str(previous[field]), 'new': str(current[field])})
    return sorted(entries, key=lambda entry: (
        entry.get('date', ''), entry.get('description', ''), entry['kind'], entry.get('field', ''),
    ))