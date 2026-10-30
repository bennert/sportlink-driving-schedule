""" Maak rijschema voor team op basis van sportlink kalender en google maps afstand en tijd """
from datetime import datetime, timedelta
import json
import os
import hashlib
import difflib
from decimal import Decimal, ROUND_HALF_UP
import requests
import icalendar
from dotenv import load_dotenv
from configuration_validation import validate_configuration
from google_maps_cache import (
    get_or_resolve_place_id,
    load_place_id_cache,
    save_place_id_cache,
)
from schedule_content import strip_travel_metrics
from schedule_change_store import update_change_report
from telegram_schedule import AMSTERDAM, select_matches_in_next_seven_days

load_dotenv()

configuration_errors = validate_configuration(os.environ)
if configuration_errors:
    raise SystemExit('Invalid configuration:\n- ' + '\n- '.join(configuration_errors))

PLACE_ID_CACHE_PATH = os.path.join('docs', 'google_maps_place_ids.json')
place_id_cache = load_place_id_cache(PLACE_ID_CACHE_PATH)

def get_google_maps_url(place):
    """ Get google maps url """
    def resolve_place_id(location):
        response = requests.get(
            'https://maps.googleapis.com/maps/api/place/findplacefromtext/json',
            params={
                'input': location,
                'inputtype': 'textquery',
                'fields': 'place_id',
                'key': os.getenv('MAPS_API_KEY'),
            },
            timeout=10,
        ).json()
        return response['candidates'][0]['place_id']

    response_place = get_or_resolve_place_id(place, place_id_cache, resolve_place_id)
    return 'https://www.google.com/maps/search/?api=1&query=Google&query_place_id='+ response_place

def get_google_maps_distance_and_duration(place):
    """ Get google maps distance """
    url_maps_distance = 'https://maps.googleapis.com/maps/api/distancematrix/json?' + \
        'units=metric&origins=51.4281731,5.3850569&destinations=' + \
        place + f'&key={os.getenv("MAPS_API_KEY")}'
    response = requests.get(url_maps_distance, timeout=10).json()
    return response['rows'][0]['elements'][0]['distance']['value'] / 1000, \
        response['rows'][0]['elements'][0]['duration']['value'] / 60

def get_sportlink_calendar(sportlink_calendar_token):
    """ Get events from sportlink """
    url_sportlink = f'https://data.sportlink.com/ical-team?token={sportlink_calendar_token}'
    response = requests.get(url_sportlink, timeout=10)
    response.raise_for_status()
    content = response.content.decode('utf-8')
    return icalendar.Calendar.from_ical(content)

def get_events_from_calendar():
    """ Get events from calendar """
    events = []
    identifiers = {}
    for event in calendar.walk('VEVENT'):
        summary = event.get('summary')
        event_start = event.get('dtstart').dt
        event_end = event.get('dtend').dt
        if event_start.tzinfo:
            event_start = event_start.astimezone(AMSTERDAM)
        if event_end.tzinfo:
            event_end = event_end.astimezone(AMSTERDAM)
        start = event_start.strftime('%H:%M')
        end = event_end.strftime('%H:%M')
        location = event.get('location')
        url_map = get_google_maps_url(location)
        location_link = f'[{location}]({url_map})'
        date = event_start.strftime('%Y-%m-%d')
        weekday = event_start.strftime('%A')
        if base_location in location:
            collection_time = (event_start - timebefore).strftime('%H:%M')
            costs = '€ 0'
        else:
            distance, duration = get_google_maps_distance_and_duration(location)

            # calculate colletion time: start - timebefore - time to travel - 5 min
            collection_time = \
                (event_start - timebefore \
                - timedelta(minutes=duration)).strftime('%H:%M')
            collection_time = collection_time[:-1] + '0'
            raw_cost = Decimal(str(distance)) * Decimal(str(travel_cost_per_km))
            rounded_cost = (raw_cost / Decimal('0.05')).quantize(
                Decimal('1'), rounding=ROUND_HALF_UP
            ) * Decimal('0.05')
            costs = f"€ {rounded_cost:.2f}"

        singleevent = [
            date, weekday, summary, collection_time, start, end, location_link, costs]
        events.append(singleevent)
        identifiers[id(singleevent)] = str(event.get('uid', ''))
    return events, identifiers

def get_events_header(language):
    """ Get events header """
    return events_header_list[language].replace("<BASE>", base_location)

def get_content_hash(content):
    """ Calculate hash of content to detect changes """
    return hashlib.md5(content.encode('utf-8')).hexdigest()

def find_old_file(directory, prefix, suffix):
    """ Find the most recent file matching pattern prefix_*_suffix """
    if not os.path.exists(directory):
        return None

    matching_files = []
    for file in os.listdir(directory):
        if file.startswith(prefix) and file.endswith(suffix):
            matching_files.append(os.path.join(directory, file))

    if not matching_files:
        return None

    # Return the most recently modified file
    return max(matching_files, key=os.path.getmtime)

def get_markdown_content(directory, prefix):
    """ Get content of the markdown file """
    old_file = find_old_file(directory, prefix, '.md')
    if old_file:
        with open(old_file, 'r', encoding='utf-8') as file_old:
            return file_old.read()
    return None

def has_content_changed(old_content, new_content):
    """ Check if file content has changed by finding old file with prefix """
    if old_content is None:
        return True
    return get_content_hash(strip_travel_metrics(old_content)) != \
        get_content_hash(strip_travel_metrics(new_content))

def print_content_diff(old_content, new_content, from_label, to_label):
    """ Print line-by-line unified diff between old and new content """
    old_lines = (old_content or '').splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)
    diff = difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile=from_label,
        tofile=to_label,
        lineterm=''
    )
    print(''.join(diff) if old_lines or new_lines else '  No content to diff')

def cleanup_old_files(directory, prefix, suffix, keep_file):
    """ Remove old files matching pattern, except the one to keep """
    if not os.path.exists(directory):
        return

    for file in os.listdir(directory):
        if file.startswith(prefix) and file.endswith(suffix):
            full_path = os.path.join(directory, file)
            if full_path != keep_file:
                try:
                    os.remove(full_path)
                    print(f'  Removed old file: {file}')
                except OSError as e:
                    print(f'  Could not remove {file}: {e}')

assert os.getenv('MAPS_API_KEY'), 'MAPS_API_KEY not set'
assert os.getenv('SPORTLINK_TOKEN_LIST'), 'SPORTLINK_TOKEN_LIST not set'
assert os.getenv('SPORTLINK_TEAM_LIST'), 'SPORTLINK_TEAM_LIST not set'

# Sportlink - combine token and list
sportlink_token_list = (os.getenv('SPORTLINK_TOKEN_LIST') or '').split(',')
sportlink_team_list = (os.getenv('SPORTLINK_TEAM_LIST') or '').split(',')

events_header_list = {
    'en': "| Date | Day | Summary | Time @<BASE> | Start | End | Location | Travel Costs |\n",
    'nl': "| Datum | Dag | Samenvatting | Tijd @<BASE> | Start | Einde | Locatie | Reis kosten |\n"
}

weekday_translation = {
    'Monday': 'Maandag',
    'Tuesday': 'Dinsdag',
    'Wednesday': 'Woensdag',
    'Thursday': 'Donderdag',
    'Friday': 'Vrijdag',
    'Saturday': 'Zaterdag',
    'Sunday': 'Zondag'
}

telegram_announcements = []
announcement_run_time = datetime.now(AMSTERDAM)

for sportlink_team in sportlink_team_list:
    team_id = sportlink_team.split(':')[0]
    base_location = sportlink_team.split(':')[1]
    warming_up_time = float(sportlink_team.split(':')[2])
    travel_cost_per_km = float(sportlink_team.split(':')[3])
    team_email = sportlink_team.split(':')[4] if len(sportlink_team.split(':')) > 4 else ''
    SPORTLINK_TOKEN = None
    for sportlink_token in sportlink_token_list:
        if sportlink_token.startswith(team_id + ':'):
            SPORTLINK_TOKEN = sportlink_token.split(':')[1]
            break
    assert SPORTLINK_TOKEN, f"Sportlink token not found for team {team_id}"

    # Check for team logo
    logo_filename_base = team_id.lower().replace(' ', '_')
    logo_team_filename = logo_filename_base + '.team.png'
    logo_club_filename = logo_filename_base + '.club.png'
    logo_team_path = os.path.join('logos', logo_team_filename)
    logo_club_path = os.path.join('logos', logo_club_filename)
    # Use forward slashes for markdown compatibility
    LOGO_TEAM_PATH_MD = f'logos/{logo_team_filename}'
    LOGO_CLUB_PATH_MD = f'logos/{logo_club_filename}'
    HAS_LOGO_TEAM = os.path.exists(logo_team_path)
    HAS_LOGO_CLUB = os.path.exists(logo_club_path)

    print(f'\nProcessing {team_id} @ base: {base_location}')
    if HAS_LOGO_TEAM:
        print(f'  Team logo found: {logo_team_path}')
    else:
        print(f'  No team logo found with expected name: {logo_team_path}')
    if HAS_LOGO_CLUB:
        print(f'  Club logo found: {logo_club_path}')
    else:
        print(f'  No club logo found with expected name: {logo_club_path}')
    # Presence time before game
    timebefore = timedelta(minutes=warming_up_time)
    calendar = get_sportlink_calendar(SPORTLINK_TOKEN)
    calendar_events, event_identifiers = get_events_from_calendar()
    # Sort events on date
    calendar_events.sort(key=lambda x: x[0])
    current_match_ids = [event_identifiers[id(event)] for event in calendar_events]
    selected_matches = select_matches_in_next_seven_days(
        calendar_events, announcement_run_time
    )
    telegram_announcements.append({
        'team_id': team_id,
        'matches': [match.copy() for match in selected_matches]
    })

    today = datetime.now().strftime("%Y-%m-%d")

    FILE_PATH_NL = f'docs/Rijschema_{team_id}_{today}.md'
    FILE_PATH_EN = f'docs/Drivingschedule_{team_id}_{today}.md'
    # Ensure the directories exist
    docs_dir = os.path.dirname(FILE_PATH_NL)
    os.makedirs(docs_dir, exist_ok=True)

    # Build content first to check if it changed
    CONTENT_EN = f'# Driving schedule {team_id}\n\n'
    # Info block with optional logos on the right
    CONTENT_EN += '<!-- INFO_START -->\n'
    CONTENT_EN += f'Base location: {base_location}\n\n'
    CONTENT_EN += f'Warming Up Time: {timebefore}\n\n'
    CONTENT_EN += f'Cost per km: €{travel_cost_per_km}\n'
    CONTENT_EN += '<!-- INFO_END -->\n'
    if HAS_LOGO_CLUB:
        CONTENT_EN += f'<!-- CLUB_LOGO: {LOGO_CLUB_PATH_MD} -->\n'
    if HAS_LOGO_TEAM:
        CONTENT_EN += f'<!-- TEAM_LOGO: {LOGO_TEAM_PATH_MD} -->\n'
    CONTENT_EN += '\n'
    CONTENT_EN += get_events_header('en')
    CONTENT_EN += '| --- | --- | --- | --- | --- | --- | --- | --- |\n'
    for calendar_event in calendar_events:
        CONTENT_EN += '| ' + ' | '.join(calendar_event) + ' |\n'

    CONTENT_NL = f'# Rijschema {team_id}\n\n'
    # Info block with optional logos on the right
    CONTENT_NL += '<!-- INFO_START -->\n'
    CONTENT_NL += f'Basis locatie: {base_location}\n\n'
    CONTENT_NL += f'Warming Up Tijd: {timebefore}\n\n'
    CONTENT_NL += f'Kosten per km: €{travel_cost_per_km}\n'
    CONTENT_NL += '<!-- INFO_END -->\n'
    if HAS_LOGO_CLUB:
        CONTENT_NL += f'<!-- CLUB_LOGO: {LOGO_CLUB_PATH_MD} -->\n'
    if HAS_LOGO_TEAM:
        CONTENT_NL += f'<!-- TEAM_LOGO: {LOGO_TEAM_PATH_MD} -->\n'
    CONTENT_NL += '\n'
    CONTENT_NL += get_events_header('nl')
    CONTENT_NL += '| --- | --- | --- | --- | --- | --- | --- | --- |\n'
    for calendar_event in calendar_events:
        calendar_event[1] = weekday_translation[calendar_event[1]]
        CONTENT_NL += '| ' + ' | '.join(calendar_event) + ' |\n'

    # Check if content changed by comparing with old files (if they exist)
    old_content_nl = get_markdown_content(docs_dir, f'Rijschema_{team_id}_')
    old_content_en = get_markdown_content(docs_dir, f'Drivingschedule_{team_id}_')
    CHANGED_NL = has_content_changed(old_content_nl, CONTENT_NL)
    CHANGED_EN = has_content_changed(old_content_en, CONTENT_EN)
    previous_sources = {}
    for old_prefix, old_source_content in ((f'Rijschema_{team_id}_', old_content_nl),
                                          (f'Drivingschedule_{team_id}_', old_content_en)):
        old_path = find_old_file(docs_dir, old_prefix, '.md')
        if old_path and old_source_content is not None:
            previous_sources[os.path.basename(old_path)] = old_source_content
    change_report, schedule_changed = update_change_report(
        docs_dir, team_id, previous_sources,
        {os.path.basename(FILE_PATH_NL): CONTENT_NL, os.path.basename(FILE_PATH_EN): CONTENT_EN},
        current_match_ids,
    )

    # Only create flag file if content changed (to trigger PDF conversion)
    if schedule_changed:
        if CHANGED_NL:
            print('  Dutch content changed - will update file and trigger PDF conversion')
            print_content_diff(old_content_nl, CONTENT_NL, f'old_Rijschema_{team_id}', f'new_Rijschema_{team_id}')
        if CHANGED_EN:
            print('  English content changed - will update file and trigger PDF conversion')
            print_content_diff(old_content_en, CONTENT_EN, f'old_Drivingschedule_{team_id}', f'new_Drivingschedule_{team_id}')

        # Clean up old files with different dates
        cleanup_old_files(docs_dir, f'Rijschema_{team_id}', '.md', FILE_PATH_NL)
        cleanup_old_files(docs_dir, f'Drivingschedule_{team_id}', '.md', FILE_PATH_EN)

        with open(FILE_PATH_NL, 'w', encoding='utf-8') as file_nl:
            file_nl.write(CONTENT_NL)

        with open(FILE_PATH_EN, 'w', encoding='utf-8') as file_en:
            file_en.write(CONTENT_EN)

        FLAG_FILE = f'docs/.convert_to_pdf_{team_id}.flag'
        print('  Content changed - flag file created for PDF conversion')
        with open(FLAG_FILE, 'w', encoding='utf-8') as f:
            f.write(f'{FILE_PATH_NL}\n{FILE_PATH_EN}\n{team_email}\n')
    else:
        print('  No changes detected - PDF conversion not needed')

with open(os.path.join('docs', 'telegram_announcements.json'), 'w', encoding='utf-8') as output_file:
    json.dump(telegram_announcements, output_file, ensure_ascii=False)

save_place_id_cache(PLACE_ID_CACHE_PATH, place_id_cache)
