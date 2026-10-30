"""Tests for Google Maps place ID cache behavior and validation."""

import json
import os
import tempfile
import unittest
from unittest.mock import Mock

from google_maps_cache import (
    get_or_resolve_place_id,
    load_place_id_cache,
    save_place_id_cache,
)


class GoogleMapsCacheTests(unittest.TestCase):
    """Verify place ID caching, persistence, and invalidation behavior."""

    def test_reuses_place_id_for_same_normalized_location(self):
        """Reuse a cached ID when the normalized location is unchanged."""
        place_ids = {}
        resolver = Mock(return_value='place-123')

        first = get_or_resolve_place_id('Sporthal, Eindhoven', place_ids, resolver)
        second = get_or_resolve_place_id('  SPORTHAL,   Eindhoven ', place_ids, resolver)

        self.assertEqual('place-123', first)
        self.assertEqual(first, second)
        resolver.assert_called_once_with('Sporthal, Eindhoven')

    def test_persists_only_place_ids_and_non_google_location_keys(self):
        """Persist place IDs without storing Google Maps URLs."""
        with tempfile.TemporaryDirectory() as directory:
            cache_path = os.path.join(directory, 'places.json')
            place_ids = {'sporthal, eindhoven': 'place-123'}

            save_place_id_cache(cache_path, place_ids)
            loaded = load_place_id_cache(cache_path)
            with open(cache_path, 'r', encoding='utf-8') as cache_file:
                serialized = json.load(cache_file)

        self.assertEqual(place_ids, loaded)
        self.assertEqual({'version', 'place_ids'}, set(serialized))
        self.assertEqual({'sporthal, eindhoven': 'place-123'}, serialized['place_ids'])

    def test_changed_location_resolves_a_new_place_id(self):
        """Resolve a fresh place ID when a location changes."""
        place_ids = {'sporthal, eindhoven': 'place-123'}
        resolver = Mock(return_value='place-456')

        result = get_or_resolve_place_id('Nieuwe sporthal, Eindhoven', place_ids, resolver)

        self.assertEqual('place-456', result)
        resolver.assert_called_once_with('Nieuwe sporthal, Eindhoven')


if __name__ == '__main__':
    unittest.main()
