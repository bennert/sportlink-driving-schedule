"""Tests for publishing stable links to the latest team schedules."""

import tempfile
import unittest
from pathlib import Path

from publish_schedule_pages import publish_latest_schedules, team_slug


class PublishSchedulePagesTests(unittest.TestCase):
    """Verify publishing picks the latest PDF and rejects empty sources."""

    def test_publishes_all_teams_and_uses_the_newest_pdf_per_team(self):
        """Publish every team using its newest available schedule PDF."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            current_pdfs = root / 'current'
            output = root / 'site'
            current_pdfs.mkdir()
            (current_pdfs / 'Rijschema_EHV HS1_2026-10-27.pdf').write_bytes(b'old schedule')
            (current_pdfs / 'Rijschema_EHV HS1_2026-10-29.pdf').write_bytes(b'latest schedule')
            (current_pdfs / 'Rijschema_EHV HS2_2026-10-28.pdf').write_bytes(b'HS2 schedule')
            (current_pdfs / 'Rijschema_EHV DS1_2026-10-26.pdf').write_bytes(b'DS1 schedule')

            published = publish_latest_schedules((current_pdfs,), output)

            self.assertEqual({'EHV DS1', 'EHV HS1', 'EHV HS2'}, set(published))
            hs1_link = output / 'teams' / f'{team_slug("EHV HS1")}.pdf'
            self.assertEqual(b'latest schedule', hs1_link.read_bytes())
            index_html = (output / 'index.html').read_text(encoding='utf-8')
            for team_id in ('EHV DS1', 'EHV HS1', 'EHV HS2'):
                with self.subTest(team_id=team_id):
                    link = f'href="teams/{team_slug(team_id)}.pdf"'
                    self.assertIn(link, index_html)
                    self.assertIn(team_id, index_html)
            self.assertIn('29-10-2026', index_html)

    def test_rejects_empty_schedule_sources(self):
        """Reject publishing when no schedule PDFs are available."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / 'empty'
            source.mkdir()

            with self.assertRaisesRegex(FileNotFoundError, 'No generated Dutch'):
                publish_latest_schedules((source,), root / 'site')


if __name__ == '__main__':
    unittest.main()
