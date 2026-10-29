import tempfile
import unittest
from pathlib import Path

from publish_schedule_pages import publish_latest_schedules, team_slug


class PublishSchedulePagesTests(unittest.TestCase):
    def test_newer_pdf_updates_the_same_team_link(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            current_pdfs = root / 'current'
            previous_pdfs = root / 'previous'
            output = root / 'site'
            current_pdfs.mkdir()
            previous_pdfs.mkdir()
            (previous_pdfs / 'Rijschema_EHV HS1_2026-10-27.pdf').write_bytes(b'old schedule')
            (current_pdfs / 'Rijschema_EHV HS1_2026-10-29.pdf').write_bytes(b'latest schedule')

            publish_latest_schedules((current_pdfs, previous_pdfs), output)

            stable_link = output / 'teams' / f'{team_slug("EHV HS1")}.pdf'
            self.assertEqual(b'latest schedule', stable_link.read_bytes())
            index_html = (output / 'index.html').read_text(encoding='utf-8')
            self.assertIn(f'href="teams/{stable_link.name}"', index_html)
            self.assertIn('EHV HS1', index_html)
            self.assertIn('29-10-2026', index_html)

    def test_rejects_empty_schedule_sources(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / 'empty'
            source.mkdir()

            with self.assertRaisesRegex(FileNotFoundError, 'No generated Dutch'):
                publish_latest_schedules((source,), root / 'site')


if __name__ == '__main__':
    unittest.main()
