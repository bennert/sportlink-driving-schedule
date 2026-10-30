"""Persist and reuse Google Maps place IDs for normalized locations."""

import json
import os


CACHE_VERSION = 1


def normalize_location(location):
    """Normalize whitespace and case for a location cache key."""
    return ' '.join(location.casefold().split())


def load_place_id_cache(path):
    """Load and validate cached place IDs from a JSON file."""
    if not os.path.exists(path):
        return {}
    with open(path, 'r', encoding='utf-8') as cache_file:
        cache_data = json.load(cache_file)
    if cache_data.get('version') != CACHE_VERSION:
        raise ValueError('Unsupported Google Maps cache version')
    place_ids = cache_data.get('place_ids')
    if not isinstance(place_ids, dict) or any(
        not isinstance(location, str) or not isinstance(place_id, str) or not place_id
        for location, place_id in place_ids.items()
    ):
        raise ValueError('Invalid Google Maps place ID cache')
    return place_ids


def save_place_id_cache(path, place_ids):
    """Write place IDs to the versioned JSON cache file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as cache_file:
        json.dump(
            {'version': CACHE_VERSION, 'place_ids': place_ids},
            cache_file,
            ensure_ascii=False,
            sort_keys=True,
        )


def get_or_resolve_place_id(location, place_ids, resolve_place_id):
    """Return a cached place ID or resolve and cache the location."""
    location_key = normalize_location(location)
    place_id = place_ids.get(location_key)
    if place_id:
        return place_id
    place_id = resolve_place_id(location)
    if not isinstance(place_id, str) or not place_id:
        raise ValueError(f'No place_id returned for location: {location}')
    place_ids[location_key] = place_id
    return place_id
