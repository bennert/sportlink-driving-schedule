from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from schedule_change_store import update_change_report
from schedule_change_text import append_workflow_summary
from test_schedule_change_store import sources
from test_schedule_changes import match_row, schedule


class WorkflowChangeSummaryTests(unittest.TestCase):
    def report(self, directory, previous=True):
        old = sources(schedule(), '29') if previous else {}
        current = sources(schedule([match_row(collection_time='10:15')]))
        return update_change_report(directory, 'EHV HS1', old, current, ['id'])[0]

    def test_changed_and_unchanged_teams_have_separate_current_run_results(self):
        with TemporaryDirectory() as directory:
            report = self.report(directory)
            path = Path(directory) / 'summary.md'
            append_workflow_summary(report, True, path)
            retained = dict(report, team_id='EHV DS1')
            append_workflow_summary(retained, False, path)
            summary = path.read_text(encoding='utf-8')
            self.assertEqual(summary.count('<h2>'), 2)
            self.assertIn('Wijzigingen in het rijschema', summary)
            self.assertIn('Driving schedule changes', summary)
            self.assertIn(report['current']['digest'], summary)
            unchanged_section = summary.split('<h2>EHV DS1</h2>')[1]
            self.assertIn('Geen schemawijzigingen', unchanged_section)
            self.assertIn('No schedule changes', unchanged_section)
            self.assertNotIn('10:15', unchanged_section)
            self.assertNotIn('coach@example.com', summary)

    def test_unavailable_comparison_is_not_reported_as_no_changes(self):
        with TemporaryDirectory() as directory:
            report = self.report(directory, previous=False)
            path = Path(directory) / 'summary.md'
            append_workflow_summary(report, True, path)
            text = path.read_text(encoding='utf-8')
            self.assertIn('Geen vorige versie beschikbaar;', text)
            self.assertIn('No previous version available;', text)
            self.assertNotIn('No schedule changes', text)

    def test_all_entries_survive_later_delivery_failure_and_source_text_is_escaped(self):
        with TemporaryDirectory() as directory:
            report = self.report(directory)
            report['entries'] = [dict(report['entries'][0], description=f'Match {index:02d} <b>&</b>')
                                 for index in range(60)]
            path = Path(directory) / 'summary.md'
            append_workflow_summary(report, True, path)
            original = path.read_bytes()
            with self.assertRaisesRegex(RuntimeError, 'Email delivery failed'):
                raise RuntimeError('Email delivery failed')
            self.assertEqual(path.read_bytes(), original)
            text = original.decode('utf-8')
            for index in range(60):
                self.assertEqual(text.count(f'Match {index:02d}'), 2)
            self.assertIn('&lt;b&gt;&amp;&lt;/b&gt;', text)
            self.assertNotIn('<b>', text)
            self.assertNotIn('Email sent successfully', text)


if __name__ == '__main__':
    unittest.main()