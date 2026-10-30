import unittest

from schedule_content import strip_travel_metrics


class ScheduleContentTests(unittest.TestCase):
    def test_old_schema_ignores_costs_and_route_columns_for_migration(self):
        old_content = (
            '| Date | Day | Summary | Collection | Start | End | Location | Costs | Kms | Minutes |\n'
            '| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n'
            '| 2026-11-01 | Sunday | Match | 10:00 | 11:00 | 13:00 | '
            '[Sports Hall](https://maps.example) | € 4.20 | 18 | 23 |\n'
        )

        normalized = strip_travel_metrics(old_content)

        self.assertIn('| <travel cost> | <route metric> | <route metric> |', normalized)
        self.assertNotIn('€ 4.20', normalized)
        self.assertEqual(normalized, strip_travel_metrics(old_content.replace('€ 4.20', '€ 4.25')))
        self.assertNotIn('https://maps.example', normalized)

        new_content = (
            '| Date | Day | Summary | Collection | Start | End | Location | Costs |\n'
            '| --- | --- | --- | --- | --- | --- | --- | --- |\n'
            '| 2026-11-01 | Sunday | Match | 10:00 | 11:00 | 13:00 | Sports Hall | € 4.20 |\n'
        )
        self.assertNotEqual(normalized, strip_travel_metrics(new_content))

    def test_new_schema_ignores_cost_and_place_url_changes(self):
        first = (
            '| 2026-11-01 | Sunday | Match | 10:00 | 11:00 | 13:00 | '
            '[Sports Hall](https://maps.example/one) | € 4.20 |\n'
        )
        second = first.replace('https://maps.example/one', 'https://maps.example/two')
        changed_cost = second.replace('€ 4.20', '€ 4.25')

        self.assertEqual(strip_travel_metrics(first), strip_travel_metrics(second))
        self.assertEqual(strip_travel_metrics(first), strip_travel_metrics(changed_cost))

    def test_ignores_cost_per_km_changes_in_both_languages(self):
        for label in ('Cost per km:', 'Kosten per km:'):
            with self.subTest(label=label):
                first = f'<!-- INFO_START -->\n{label} EUR 0.23\n<!-- INFO_END -->\n'
                second = first.replace('0.23', '0.25')

                self.assertEqual(strip_travel_metrics(first), strip_travel_metrics(second))

    def test_preserves_schedule_changes(self):
        first = (
            '| 2026-11-01 | Sunday | Match | 10:00 | 11:00 | 13:00 | '
            '[Sports Hall](https://maps.example) | EUR 4.20 |\n'
        )
        for original, replacement in (
            ('2026-11-01', '2026-11-02'),
            ('Sunday', 'Monday'),
            ('Match', 'Other match'),
            ('10:00', '10:10'),
            ('11:00', '11:30'),
            ('13:00', '13:30'),
            ('Sports Hall', 'Other Hall'),
        ):
            with self.subTest(field=original):
                self.assertNotEqual(
                    strip_travel_metrics(first),
                    strip_travel_metrics(first.replace(original, replacement)),
                )


if __name__ == '__main__':
    unittest.main()