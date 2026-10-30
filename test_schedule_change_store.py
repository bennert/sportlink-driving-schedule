from contextlib import chdir, redirect_stdout
from io import StringIO
import json
import os
from pathlib import Path
import runpy
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from schedule_change_store import load_change_report, report_path, update_change_report
from test_configuration_validation import VALID_CONFIGURATION
from test_schedule_changes import match_row, schedule


def sources(content, day='30'):
    return {f'Drivingschedule_EHV HS1_2026-10-{day}.md': content,
            f'Rijschema_EHV HS1_2026-10-{day}.md': content.replace('Sunday', 'Zondag')}


class ChangeStoreTests(unittest.TestCase):
    def test_generator_preserves_source_uids_and_does_not_notify_on_unchanged_run(self):
        script = Path(__file__).with_name('create_driving_schedule.py')
        calendar = (
            'BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//Test//EN\r\nBEGIN:VEVENT\r\n'
            'UID:stable-match\r\nDTSTART:20261101T{start}0000Z\r\n'
            'DTEND:20261101T{end}0000Z\r\nSUMMARY:EHV HS1 - Team A\r\n'
            'LOCATION:Club Hall\r\nEND:VEVENT\r\nEND:VCALENDAR\r\n'
        )
        with TemporaryDirectory() as directory, chdir(directory), redirect_stdout(StringIO()), \
                patch.dict(os.environ, VALID_CONFIGURATION, clear=True), \
                patch('dotenv.load_dotenv'), patch('requests.get') as request:
            request.return_value.json.return_value = {'candidates': [{'place_id': 'place-1'}]}
            request.return_value.content = calendar.format(start='10', end='12').encode()
            runpy.run_path(str(script), run_name='__main__')
            first = load_change_report('docs', 'EHV HS1', required=True)
            self.assertEqual(first['comparison'], 'missing')
            self.assertEqual(first['snapshot']['matches'][0]['uid'], 'stable-match')
            self.assertEqual(first['snapshot']['matches'][0]['start_time'], '11:00')
            request.return_value.content = calendar.format(start='11', end='13').encode()
            runpy.run_path(str(script), run_name='__main__')
            updated = load_change_report('docs', 'EHV HS1', required=True)
            self.assertEqual(updated['comparison'], 'compared')
            self.assertEqual({entry['field'] for entry in updated['entries']},
                             {'collection_time', 'start_time', 'end_time'})
            Path('docs/.convert_to_pdf_EHV HS1.flag').unlink()
            runpy.run_path(str(script), run_name='__main__')
            self.assertEqual(load_change_report('docs', 'EHV HS1', required=True), updated)
            self.assertFalse(Path('docs/.convert_to_pdf_EHV HS1.flag').exists())

    def test_artifact_round_trip_without_previous_files_retains_uids_and_baseline(self):
        with TemporaryDirectory() as directory:
            first_sources = sources(schedule(), '29')
            first, changed = update_change_report(directory, 'EHV HS1', {}, first_sources, ['stable-id'])
            self.assertTrue(changed)
            current_sources = sources(schedule([match_row(collection_time='10:15')]))
            report, changed = update_change_report(
                directory, 'EHV HS1', first_sources, current_sources, ['stable-id'])
            self.assertTrue(changed)
            self.assertEqual(len(report['entries']), 1)
            self.assertEqual(report['baseline'], first['current'])
            for name, content in current_sources.items():
                (Path(directory) / name).write_text(content, encoding='utf-8')
            restored = load_change_report(directory, 'EHV HS1', required=True)
            self.assertEqual(restored, report)
            self.assertEqual(restored['snapshot']['matches'][0]['uid'], 'stable-id')

    def test_unchanged_run_preserves_report_and_does_not_request_email(self):
        with TemporaryDirectory() as directory:
            previous = sources(schedule(), '29')
            current = sources(schedule([match_row(collection_time='10:15')]))
            report, _ = update_change_report(directory, 'EHV HS1', previous, current, ['id'])
            raw = report_path(directory, 'EHV HS1').read_bytes()
            ignored_change = sources(schedule([match_row(collection_time='10:15')]).replace('0.23', '0.50'), '31')
            retained, changed = update_change_report(directory, 'EHV HS1', current, ignored_change, ['id'])
            self.assertFalse(changed)
            self.assertEqual(retained, report)
            self.assertEqual(report_path(directory, 'EHV HS1').read_bytes(), raw)

    def test_missing_legacy_sidecar_does_not_invent_historical_changes(self):
        with TemporaryDirectory() as directory:
            current = sources(schedule())
            report, changed = update_change_report(directory, 'EHV HS1', current, current, ['id'])
            self.assertFalse(changed)
            self.assertEqual(report['comparison'], 'legacy')
            self.assertEqual(report['entries'], [])

    def test_rejects_missing_invalid_and_wrong_version_reports(self):
        with TemporaryDirectory() as directory:
            current = sources(schedule())
            path = report_path(directory, 'EHV HS1')
            with self.assertRaisesRegex(ValueError, 'EHV HS1'):
                load_change_report(directory, 'EHV HS1', current, required=True)
            path.write_text('invalid JSON', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'EHV HS1'):
                load_change_report(directory, 'EHV HS1', current, required=True)
            path.unlink()
            report, _ = update_change_report(directory, 'EHV HS1', {}, current, ['id'])
            for field, value in (('schema_version', 99), ('team_id', 'Other team'),
                                 ('entries', [{}]), ('snapshot', {}), ('comparison', 'unknown')):
                with self.subTest(field=field):
                    invalid = dict(report, **{field: value})
                    path.write_text(json.dumps(invalid), encoding='utf-8')
                    with self.assertRaisesRegex(ValueError, 'EHV HS1'):
                        load_change_report(directory, 'EHV HS1', current, required=True)
            path.write_text(json.dumps(report), encoding='utf-8')
            wrong_sources = sources(schedule([match_row(collection_time='10:15')]))
            with self.assertRaisesRegex(ValueError, 'EHV HS1'):
                load_change_report(directory, 'EHV HS1', wrong_sources, required=True)


if __name__ == '__main__':
    unittest.main()