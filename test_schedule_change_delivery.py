from contextlib import chdir, redirect_stdout
from io import StringIO
import os
from pathlib import Path
import runpy
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from schedule_change_store import report_path, update_change_report
from schedule_change_text import bilingual_report, report_lines
from test_configuration_validation import VALID_CONFIGURATION
from test_schedule_change_store import sources
from test_schedule_changes import match_row, schedule


class ChangeDeliveryTests(unittest.TestCase):
    def report(self, directory, previous=True):
        old = sources(schedule(), '29') if previous else {}
        current = sources(schedule([match_row(collection_time='10:15')]))
        return update_change_report(directory, 'EHV HS1', old, current, ['id'])[0], current

    def test_bilingual_rendering_keeps_all_entries_and_localizes_dates(self):
        with TemporaryDirectory() as directory:
            report, _ = self.report(directory)
            entry = report['entries'][0]
            report['entries'] = [dict(entry, description=f'Match {index:02d}') for index in range(60)]
            for language in ('nl', 'en'):
                lines = report_lines(report, language)
                self.assertEqual(len([line for line in lines if line.startswith('- ')]), 60)
                self.assertIn('Match 00', lines[3])
                self.assertIn('Match 59', lines[-1])
                self.assertIn('01-11-2026', lines[-1])
                self.assertNotIn('EUR', '\n'.join(lines))

    def test_missing_baseline_notice_is_bilingual_without_invented_entries(self):
        with TemporaryDirectory() as directory:
            report, _ = self.report(directory, previous=False)
            text = bilingual_report(report)
            self.assertIn('Geen vorige versie beschikbaar;', text)
            self.assertIn('No previous version available;', text)
            self.assertNotIn('Toegevoegd:', text)
            self.assertNotIn('Added:', text)

    def test_email_keeps_both_pdfs_and_puts_bilingual_report_before_attachments(self):
        self.run_email(invalid_report=False)

    def test_email_is_not_sent_with_invalid_report(self):
        self.run_email(invalid_report=True)

    def run_email(self, invalid_report):
        script = Path(__file__).with_name('send_team_emails.py')
        with TemporaryDirectory() as directory, chdir(directory), redirect_stdout(StringIO()):
            docs = Path(directory) / 'docs'
            docs.mkdir()
            _report, current = self.report(docs)
            for name, content in current.items():
                (docs / name).write_text(content, encoding='utf-8')
                (docs / name).with_suffix('.pdf').write_bytes(b'test PDF')
            names = list(current)
            (docs / '.convert_to_pdf_EHV HS1.flag').write_text(
                f'docs/{names[1]}\ndocs/{names[0]}\ncoach@example.com\n', encoding='utf-8')
            if invalid_report:
                report_path(docs, 'EHV HS1').write_text('invalid JSON', encoding='utf-8')
            with patch.dict(os.environ, VALID_CONFIGURATION, clear=True), \
                    patch('dotenv.load_dotenv'), patch('os.path.dirname', return_value=directory), \
                    patch('smtplib.SMTP_SSL') as smtp:
                if invalid_report:
                    with self.assertRaises(SystemExit) as result:
                        runpy.run_path(str(script), run_name='__main__')
                    self.assertEqual(result.exception.code, 1)
                    smtp.assert_not_called()
                else:
                    runpy.run_path(str(script), run_name='__main__')
                    message = smtp.return_value.send_message.call_args.args[0]
                    body = message.get_payload()[0].get_payload(decode=True).decode('utf-8')
                    self.assertLess(body.index('Driving schedule changes'), body.index('See the attached'))
                    self.assertIn('Wijzigingen in het rijschema', body)
                    self.assertEqual(body.count('10:00'), 2)
                    self.assertEqual(body.count('10:15'), 2)
                    self.assertEqual(message['To'], 'coach@example.com')
                    self.assertEqual(len(message.get_payload()), 3)


if __name__ == '__main__':
    unittest.main()