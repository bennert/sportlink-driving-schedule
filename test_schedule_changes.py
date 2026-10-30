import unittest

from schedule_changes import MATCH_FIELDS, compare_schedules, parse_schedule


def schedule(rows=None, language='en', base='Eindhoven', warming_up='0:45:00', extra=''):
    labels = ('Base location', 'Warming Up Time', 'Cost per km') if language == 'en' else (
        'Basis locatie', 'Warming Up Tijd', 'Kosten per km')
    header = 'Date | Day | Summary | Collection | Start | End | Location | Costs'
    if language == 'nl':
        header = 'Datum | Dag | Samenvatting | Verzamelen | Start | Einde | Locatie | Kosten'
    content = (f'# Driving schedule EHV HS1\n{labels[0]}: {base}\n'
               f'{labels[1]}: {warming_up}\n{labels[2]}: EUR 0.23\n{extra}'
               f'| {header} |\n| --- | --- | --- | --- | --- | --- | --- | --- |\n')
    for row in rows if rows is not None else [match_row()]:
        content += '| ' + ' | '.join(row) + ' |\n'
    return content


def match_row(**changes):
    values = dict(zip(MATCH_FIELDS, (
        '2026-11-01', 'Sunday', 'EHV HS1 - Team A', '10:00', '11:00', '13:00',
        '[Hall A](https://maps.example/one)',
    )))
    values.update(changes)
    return [values[field] for field in MATCH_FIELDS] + ['EUR 4.20']


class ScheduleComparisonTests(unittest.TestCase):
    def test_all_match_fields_show_old_and_new_values_with_unique_uid(self):
        replacements = ('2026-11-08', 'Monday', 'Team B', '10:15', '11:30', '13:30', 'Hall B')
        previous = parse_schedule(schedule(), ['source-1'])
        for field, value in zip(MATCH_FIELDS, replacements):
            with self.subTest(field=field):
                current = parse_schedule(schedule([match_row(**{field: value})]), ['source-1'])
                entries = compare_schedules(previous, current)
                self.assertEqual(len(entries), 1)
                self.assertEqual(entries[0]['field'], field)
                self.assertEqual(entries[0]['old'], previous['matches'][0][field])
                self.assertEqual(entries[0]['new'], value)

    def test_unique_legacy_row_matches_without_source_id(self):
        entries = compare_schedules(parse_schedule(schedule()), parse_schedule(
            schedule([match_row(collection_time='10:15')]), ['newly-available-id']))
        self.assertEqual([entry['kind'] for entry in entries], ['modified'])

    def test_date_or_description_change_without_identifier_is_remove_and_add(self):
        for changes in ({'date': '2026-11-08'}, {'description': 'Other match'}):
            with self.subTest(changes=changes):
                entries = compare_schedules(parse_schedule(schedule()), parse_schedule(
                    schedule([match_row(**changes)])))
                self.assertCountEqual([entry['kind'] for entry in entries], ['removed', 'added'])

    def test_different_source_ids_are_not_matched_by_description(self):
        entries = compare_schedules(parse_schedule(schedule(), ['old']),
                                    parse_schedule(schedule(), ['new']))
        self.assertCountEqual([entry['kind'] for entry in entries], ['removed', 'added'])

    def test_additions_and_removals_leave_unchanged_matches_out(self):
        old = schedule([match_row(), match_row(date='2026-11-08', description='B')])
        new = schedule([match_row(), match_row(date='2026-11-15', description='C')])
        entries = compare_schedules(parse_schedule(old), parse_schedule(new))
        self.assertEqual([(entry['kind'], entry['description']) for entry in entries],
                         [('removed', 'B'), ('added', 'C')])

    def test_ambiguous_duplicates_preserve_counts(self):
        old = schedule([match_row(), match_row(start_time='15:00')])
        new = schedule([match_row(start_time='11:30'), match_row(start_time='15:30')])
        entries = compare_schedules(parse_schedule(old), parse_schedule(new))
        self.assertCountEqual([entry['kind'] for entry in entries], ['removed'] * 2 + ['added'] * 2)
        self.assertEqual(compare_schedules(parse_schedule(old), parse_schedule(old)), [])

    def test_settings_logos_and_document_changes_are_not_match_changes(self):
        old = parse_schedule(schedule(extra='<!-- CLUB_LOGO: logos/old.png -->\n'))
        new = parse_schedule(schedule(base='Veldhoven', warming_up='1:00:00',
                                      extra='<!-- CLUB_LOGO: logos/new.png -->\nOther information\n'))
        entries = compare_schedules(old, new)
        self.assertEqual(len(entries), 4)
        self.assertEqual({entry['kind'] for entry in entries}, {'setting', 'document'})
        logo = next(entry for entry in entries if entry['field'] == 'club_logo')
        self.assertEqual((logo['old'], logo['new']), ('logos/old.png', 'logos/new.png'))

    def test_dutch_and_english_rows_have_the_same_meaning(self):
        english = parse_schedule(schedule())
        dutch = parse_schedule(schedule([match_row(weekday='Zondag')], language='nl'))
        self.assertEqual(compare_schedules(english, dutch), [])

    def test_invalid_baselines_are_not_empty_schedules(self):
        for content in ('', 'Not a schedule', schedule().replace('2026-11-01', 'not-a-date')):
            with self.subTest(content=content):
                with self.assertRaises(ValueError):
                    parse_schedule(content)
        self.assertEqual(parse_schedule(schedule([]))['matches'], [])


if __name__ == '__main__':
    unittest.main()