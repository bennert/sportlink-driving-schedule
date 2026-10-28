import unittest

from schedule_content import strip_travel_metrics


class ScheduleContentTests(unittest.TestCase):
    def test_old_schema_keeps_costs_but_ignores_route_columns_for_migration(self):
        old_content = (
            '| Date | Day | Summary | Collection | Start | End | Location | Costs | Kms | Minutes |\n'
            '| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n'
            '| 2026-11-01 | Sunday | Match | 10:00 | 11:00 | 13:00 | '
            '[Sports Hall](https://maps.example) | € 4.20 | 18 | 23 |\n'
        )

        normalized = strip_travel_metrics(old_content)

        self.assertIn('| Costs | <route metric> | <route metric> |', normalized)
        self.assertIn('| € 4.20 | <route metric> | <route metric> |', normalized)
        self.assertNotIn('https://maps.example', normalized)

        new_content = (
            '| Date | Day | Summary | Collection | Start | End | Location | Costs |\n'
            '| --- | --- | --- | --- | --- | --- | --- | --- |\n'
            '| 2026-11-01 | Sunday | Match | 10:00 | 11:00 | 13:00 | Sports Hall | € 4.20 |\n'
        )
        self.assertNotEqual(normalized, strip_travel_metrics(new_content))

    def test_new_schema_preserves_cost_changes_and_ignores_place_url_changes(self):
        first = (
            '| 2026-11-01 | Sunday | Match | 10:00 | 11:00 | 13:00 | '
            '[Sports Hall](https://maps.example/one) | € 4.20 |\n'
        )
        second = first.replace('https://maps.example/one', 'https://maps.example/two')
        changed_cost = second.replace('€ 4.20', '€ 4.25')

        self.assertEqual(strip_travel_metrics(first), strip_travel_metrics(second))
        self.assertNotEqual(strip_travel_metrics(first), strip_travel_metrics(changed_cost))


if __name__ == '__main__':
    unittest.main()