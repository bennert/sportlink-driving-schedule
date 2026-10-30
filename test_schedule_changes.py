import unittest

from schedule_changes import (
    MATCH_FIELDS, build_change_report, compare_schedules, comparison_notice, parse_schedule,
)


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

    def test_costs_and_map_urls_are_ignored_alone_and_with_a_time_change(self):
        for language in ('nl', 'en'):
            previous = schedule(language=language)
            changed = previous.replace('EUR 4.20', 'EUR 9.99').replace('0.23', '0.50').replace(
                'https://maps.example/one', 'https://maps.example/two')
            with self.subTest(language=language):
                self.assertEqual(compare_schedules(parse_schedule(previous), parse_schedule(changed)), [])
                entries = compare_schedules(parse_schedule(previous), parse_schedule(
                    changed.replace('10:00', '10:15')))
                self.assertEqual(len(entries), 1)
                self.assertEqual(entries[0]['field'], 'collection_time')

    def test_legacy_route_metric_values_are_ignored_but_schema_migration_is_not(self):
        previous = schedule().replace('Costs |', 'Costs | Kms | Minutes |').replace(
            'EUR 4.20 |', 'EUR 4.20 | 18 | 23 |').replace(
            '| --- | --- | --- | --- | --- | --- | --- | --- |',
            '| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |')
        changed = previous.replace('18 | 23', '19 | 24')
        self.assertEqual(compare_schedules(parse_schedule(previous), parse_schedule(changed)), [])
        entries = compare_schedules(parse_schedule(previous), parse_schedule(schedule()))
        self.assertEqual([(entry['kind'], entry['field']) for entry in entries], [('document', 'columns')])


class ComparisonBaselineTests(unittest.TestCase):
    def report(self, previous, current=None):
        return build_change_report('EHV HS1', previous, current or schedule(),
                                   'Drivingschedule_EHV HS1_2026-10-30.md',
                                   'Drivingschedule_EHV HS1_2026-10-30.md')

    def test_same_day_versions_have_distinct_digests_without_delivery_claims(self):
        report = self.report(schedule(), schedule([match_row(collection_time='10:15')]))
        self.assertEqual(report['comparison'], 'compared')
        baseline = dict(report['baseline'] or {})
        self.assertTrue(baseline)
        self.assertEqual(baseline['filename'], report['current']['filename'])
        self.assertNotEqual(baseline['digest'], report['current']['digest'])
        for language in ('nl', 'en'):
            notice = comparison_notice(report, language)
            self.assertIn(baseline['filename'], notice)
            self.assertIn(baseline['digest'], notice)
            self.assertNotIn('delivered', notice)

    def test_missing_and_unreadable_baselines_have_exact_bilingual_notices(self):
        expected = {
            'missing': (
                'Geen vorige versie beschikbaar; wijzigingen konden niet worden bepaald',
                'No previous version available; changes could not be determined'),
            'unreadable': (
                'Vorige versie onleesbaar; wijzigingen konden niet worden bepaald',
                'Previous version unreadable; changes could not be determined'),
        }
        for previous, status in ((None, 'missing'), ('not a schedule', 'unreadable')):
            with self.subTest(status=status):
                report = self.report(previous)
                self.assertEqual(report['comparison'], status)
                self.assertEqual(report['entries'], [])
                self.assertEqual(len(report['snapshot']['matches']), 1)
                self.assertEqual(tuple(comparison_notice(report, lang) for lang in ('nl', 'en')),
                                 expected[status])

    def test_readable_legacy_baseline_does_not_require_identifier_metadata(self):
        report = self.report(schedule(), schedule([match_row(collection_time='10:15')]))
        self.assertEqual(report['comparison'], 'compared')
        self.assertEqual(len(report['entries']), 1)

    def test_invalid_current_schedule_is_not_presented_as_success(self):
        with self.assertRaises(ValueError):
            self.report(schedule(), 'unavailable calendar')


if __name__ == '__main__':
    unittest.main()