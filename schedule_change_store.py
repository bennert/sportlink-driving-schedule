import json
from pathlib import Path
import re

from schedule_changes import MATCH_FIELDS, build_change_report, parse_schedule, version_reference
from schedule_content import strip_travel_metrics


def report_path(directory, team_id):
    return Path(directory) / f'schedule_changes_{team_id}.json'


def _primary(sources):
    return next((name for name in sources if name.startswith('Drivingschedule_')), next(iter(sources)))


def _valid_reference(reference):
    return (isinstance(reference, dict) and isinstance(reference.get('filename'), str)
            and Path(reference['filename']).name == reference['filename']
            and isinstance(reference.get('digest'), str)
            and re.fullmatch(r'[0-9a-f]{64}', reference['digest']) is not None)


def _validate_report(report, team_id, sources):
    if report['schema_version'] != 1 or report['team_id'] != team_id:
        raise ValueError('Unsupported schema or incorrect team')
    if report['comparison'] not in ('compared', 'missing', 'unreadable', 'legacy'):
        raise ValueError('Unknown comparison status')
    if not _valid_reference(report['current']):
        raise ValueError('Invalid current version')
    if report['comparison'] in ('compared', 'unreadable') and not _valid_reference(report['baseline']):
        raise ValueError('Invalid baseline version')
    if report['comparison'] in ('missing', 'legacy') and report['baseline'] is not None:
        raise ValueError('Unexpected baseline version')
    if not isinstance(report['sources'], dict) or set(report['sources']) != set(sources):
        raise ValueError('Incorrect source versions')
    for name, content in sources.items():
        if not name.startswith((f'Drivingschedule_{team_id}_', f'Rijschema_{team_id}_')):
            raise ValueError('Incorrect source team')
        if Path(name).name != name or report['sources'][name] != version_reference(name, content)['digest']:
            raise ValueError(f'Incorrect source version: {name}')
    current_name = report['current']['filename']
    if report['sources'].get(current_name) != report['current']['digest']:
        raise ValueError('Incorrect current version digest')
    identifiers = [match.get('uid') for match in report['snapshot']['matches']]
    if any(identifier is not None and not isinstance(identifier, str) for identifier in identifiers):
        raise ValueError('Invalid source match identifier')
    if parse_schedule(sources[current_name], identifiers) != report['snapshot']:
        raise ValueError('Snapshot does not match the current version')
    if not isinstance(report['entries'], list):
        raise ValueError('Invalid change entries')
    if report['comparison'] != 'compared' and report['entries']:
        raise ValueError('Unavailable comparisons cannot contain match changes')
    for entry in report['entries']:
        if entry['kind'] not in ('added', 'removed', 'modified', 'setting', 'document'):
            raise ValueError('Unknown change category')
        if entry['kind'] in ('added', 'removed', 'modified'):
            if not all(isinstance(entry[field], str) for field in ('date', 'description')):
                raise ValueError('Invalid match identity')
        if entry['kind'] in ('added', 'removed'):
            if not all(isinstance(entry['match'][field], str) for field in MATCH_FIELDS):
                raise ValueError('Invalid added or removed match')
        elif not all(isinstance(entry[field], str) for field in ('field', 'old', 'new')):
            raise ValueError('Invalid old and new values')


def load_change_report(directory, team_id, sources=None, required=False):
    path = report_path(directory, team_id)
    if not path.exists() and not required:
        return None
    try:
        report = json.loads(path.read_text(encoding='utf-8'))
        if sources is None:
            names = report['sources']
            if not isinstance(names, dict) or any(Path(name).name != name for name in names):
                raise ValueError('Invalid source filenames')
            sources = {name: (Path(directory) / name).read_text(encoding='utf-8') for name in names}
        _validate_report(report, team_id, sources)
        return report
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        raise ValueError(f'Change report error for {team_id} ({path.name}): {error}') from error


def update_change_report(directory, team_id, previous_sources, current_sources, current_ids):
    retained = load_change_report(directory, team_id, previous_sources) if previous_sources else None
    old_by_language = {name.split('_', 1)[0]: content for name, content in previous_sources.items()}
    changed = any(strip_travel_metrics(content) != strip_travel_metrics(
        old_by_language.get(name.split('_', 1)[0], '')) for name, content in current_sources.items())
    if not changed and retained:
        return retained, False
    selected_sources = current_sources if changed else previous_sources
    current_name = _primary(selected_sources)
    previous_name = _primary(previous_sources) if previous_sources else ''
    previous_ids = None
    if retained and retained['current']['filename'] == previous_name:
        previous_ids = [match.get('uid') for match in retained['snapshot']['matches']]
    report = build_change_report(
        team_id, previous_sources.get(previous_name), selected_sources[current_name],
        previous_name, current_name, previous_ids, current_ids,
    )
    if not changed:
        report.update(comparison='legacy', baseline=None, entries=[])
    elif report['comparison'] == 'compared' and not report['entries']:
        report['entries'] = [{'kind': 'document', 'field': 'document',
                              'old': 'Previous document', 'new': 'Updated document'}]
    report['sources'] = {name: version_reference(name, content)['digest']
                         for name, content in selected_sources.items()}
    _validate_report(report, team_id, selected_sources)
    path = report_path(directory, team_id)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temporary.replace(path)
    return report, changed