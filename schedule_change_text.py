from datetime import datetime
from html import escape
from pathlib import Path

from schedule_changes import WEEKDAYS, comparison_notice


HEADINGS = {'nl': 'Wijzigingen in het rijschema', 'en': 'Driving schedule changes'}
FIELD_LABELS = {
    'date': ('Datum', 'Date'), 'weekday': ('Dag', 'Day'),
    'description': ('Wedstrijd', 'Match'), 'collection_time': ('Verzamelen', 'Collection time'),
    'start_time': ('Aanvang', 'Start'), 'end_time': ('Einde', 'End'),
    'location': ('Locatie', 'Location'), 'base_location': ('Basislocatie', 'Base location'),
    'warming_up_time': ('Warming-uptijd', 'Warming-up time'),
    'club_logo': ('Clublogo', 'Club logo'), 'team_logo': ('Teamlogo', 'Team logo'),
    'document': ('Documentinformatie', 'Document information'),
    'columns': ('Tabelindeling', 'Table layout'),
}


def _value(field, value, language):
    if not value:
        return 'Niet ingesteld' if language == 'nl' else 'Not set'
    if field == 'date':
        return datetime.strptime(value, '%Y-%m-%d').strftime('%d-%m-%Y')
    if field == 'weekday' and language == 'nl':
        return {english: dutch for dutch, english in WEEKDAYS.items()}.get(value, value)
    if field == 'warming_up_time' and value.count(':') == 2:
        hours, minutes, _seconds = value.split(':')
        return f'{int(hours):02d}:{minutes}'
    return value


def entry_text(entry, language):
    language_index = 0 if language == 'nl' else 1
    kind = entry['kind']
    if kind in ('added', 'removed'):
        labels = {'added': ('Toegevoegd', 'Added'),
                  'removed': ('Vervallen uit het schema', 'Removed from the schedule')}
        match = entry['match']
        details = ' | '.join(
            f'{FIELD_LABELS[field][language_index]}: {_value(field, match[field], language)}'
            for field in ('collection_time', 'start_time', 'end_time', 'location')
        )
        return (f"{labels[kind][language_index]}: {_value('date', match['date'], language)} | "
                f"{match['description']} | {details}")
    field = entry['field']
    label = FIELD_LABELS.get(field, FIELD_LABELS['document'])[language_index]
    old_value, new_value = (_value(field, entry[key], language) for key in ('old', 'new'))
    if kind == 'modified':
        prefix = f"{_value('date', entry['date'], language)} | {entry['description']} | "
    elif kind == 'document':
        prefix = 'Documentinformatie gewijzigd | ' if language == 'nl' else 'Document information changed | '
    else:
        prefix = ''
    connector = 'naar' if language == 'nl' else 'to'
    return f'{prefix}{label}: {old_value} {connector} {new_value}'


def report_lines(report, language):
    current = report['current']
    label = 'Huidige versie' if language == 'nl' else 'Current version'
    lines = [f"{HEADINGS[language]} - {report['team_id']}",
             f"{label}: {current['filename']} ({current['digest']})",
             comparison_notice(report, language)]
    lines.extend('- ' + entry_text(entry, language) for entry in report['entries'])
    if report['comparison'] == 'compared' and not report['entries']:
        lines.append('Geen schemawijzigingen' if language == 'nl' else 'No schedule changes')
    return lines


def bilingual_report(report):
    return '\n'.join(report_lines(report, 'nl')) + '\n\n' + '\n'.join(report_lines(report, 'en'))


def append_workflow_summary(report, changed, summary_path):
    if not summary_path:
        return
    text = bilingual_report(report) if changed else 'Geen schemawijzigingen\nNo schedule changes'
    section = f"<h2>{escape(report['team_id'])}</h2>\n<pre>{escape(text)}</pre>\n\n"
    with Path(summary_path).open('a', encoding='utf-8') as summary:
        summary.write(section)