from contextlib import chdir, redirect_stdout
from io import StringIO
from pathlib import Path
import runpy
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import pymupdf

from schedule_change_store import report_path, update_change_report
from test_schedule_change_store import sources
from test_schedule_changes import match_row, schedule


def convert_pdfs(directory, current):
    script = Path(__file__).with_name('convert_driving_schedule_to_pdf.py')
    docs = Path(directory) / 'docs'
    docs.mkdir(exist_ok=True)
    for name, content in current.items():
        (docs / name).write_text(content, encoding='utf-8')
    with chdir(directory), redirect_stdout(StringIO()), \
            patch('os.path.dirname', return_value=str(directory)), \
            patch('sys.argv', [str(script), '--all']):
        runpy.run_path(str(script), run_name='__main__')
    return [docs / name.replace('.md', '.pdf') for name in current]


class ChangePdfTests(unittest.TestCase):
    def test_localized_report_follows_complete_schedule_on_a_new_page(self):
        with TemporaryDirectory() as directory:
            docs = Path(directory) / 'docs'
            docs.mkdir()
            previous = sources(schedule([match_row(), match_row(date='2026-11-08', description='Removed')]), '29')
            current = sources(schedule([match_row(collection_time='10:15')]))
            update_change_report(docs, 'EHV HS1', previous, current, ['id'])
            for path in convert_pdfs(directory, current):
                with pymupdf.open(path) as document:
                    self.assertGreaterEqual(len(document), 2)
                    table = document[0].get_text()
                    report = '\n'.join(page.get_text() for page in list(document)[1:])
                    self.assertIn('EUR 4.20', table)
                    self.assertIn('EHV HS1 - Team A', table)
                    self.assertNotIn('EUR 4.20', report)
                    self.assertIn('10:00', report)
                    self.assertIn('10:15', report)
                    self.assertIn('01-11-2026', report)
                    self.assertIn('EHV HS1', report)
                    if path.name.startswith('Rijschema_'):
                        self.assertIn('Wijzigingen in het rijschema', report)
                        self.assertIn('Vervallen uit het schema', report)
                        self.assertNotIn('Driving schedule changes', report)
                    else:
                        self.assertIn('Driving schedule changes', report)
                        self.assertIn('Removed from the schedule', report)
                        self.assertNotIn('Wijzigingen in het rijschema', report)

    def test_missing_unreadable_and_legacy_notices(self):
        for state, previous in (('missing', {}), ('unreadable', sources('not a schedule', '29')),
                                ('legacy', None)):
            with self.subTest(state=state), TemporaryDirectory() as directory:
                docs = Path(directory) / 'docs'
                docs.mkdir()
                current = sources(schedule())
                if previous is not None:
                    update_change_report(docs, 'EHV HS1', previous, current, ['id'])
                for path in convert_pdfs(directory, current):
                    with pymupdf.open(path) as document:
                        text = document[-1].get_text()
                        notices = {
                            'missing': ('Geen vorige versie beschikbaar;', 'No previous version available;'),
                            'unreadable': ('Vorige versie onleesbaar;', 'Previous version unreadable;'),
                            'legacy': ('Wijzigingsoverzicht niet beschikbaar', 'Change report unavailable'),
                        }
                        self.assertIn(notices[state][0 if path.name.startswith('Rijschema_') else 1], text)
                        self.assertNotIn('Toegevoegd:', text)
                        self.assertNotIn('Added:', text)

    def test_required_invalid_or_missing_report_blocks_generation(self):
        for invalid in (None, 'invalid JSON'):
            with self.subTest(invalid=invalid), TemporaryDirectory() as directory:
                docs = Path(directory) / 'docs'
                docs.mkdir()
                (docs / '.convert_to_pdf_EHV HS1.flag').touch()
                if invalid:
                    report_path(docs, 'EHV HS1').write_text(invalid, encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'EHV HS1'):
                    convert_pdfs(directory, sources(schedule()))
                self.assertEqual(list(docs.glob('*.pdf')), [])

    def test_long_report_paginates_without_clipping_overlap_or_lost_entries(self):
        with TemporaryDirectory() as directory:
            docs = Path(directory) / 'docs'
            docs.mkdir()
            old_rows = [match_row(description=f'Match {index:02d}') for index in range(60)]
            new_rows = [match_row(description=f'Match {index:02d}', location='Long venue name ' * 6)
                        for index in range(60)]
            current = sources(schedule(new_rows))
            update_change_report(docs, 'EHV HS1', sources(schedule(old_rows), '29'), current,
                                 [f'match-{index}' for index in range(60)])
            for path in convert_pdfs(directory, current):
                with pymupdf.open(path) as document:
                    report_start = next(index for index, page in enumerate(document)
                                        if 'schemawijzigingen' in page.get_text().lower()
                                        or 'Wijzigingen in het rijschema' in page.get_text()
                                        or 'Driving schedule changes' in page.get_text())
                    pages = list(document)[report_start:]
                    self.assertGreater(len(pages), 1)
                    text = '\n'.join(page.get_text() for page in pages)
                    for index in range(60):
                        self.assertEqual(text.count(f'Match {index:02d}'), 1)
                    for page in pages:
                        pixmap = page.get_pixmap(matrix=pymupdf.Matrix(0.5, 0.5), colorspace=pymupdf.csGRAY)
                        self.assertLess(min(pixmap.samples), 200)
                        line_boxes = [pymupdf.Rect(line['bbox'])
                                      for block in page.get_text('dict')['blocks'] if 'lines' in block
                                      for line in block['lines']]
                        for index, box in enumerate(line_boxes):
                            self.assertTrue(page.rect.contains(box))
                            for other in line_boxes[index + 1:]:
                                self.assertLess((box & other).get_area(), 0.1)


if __name__ == '__main__':
    unittest.main()