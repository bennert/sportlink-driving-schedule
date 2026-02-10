""" Maak rijschema voor team op basis van sportlink kalender en google maps afstand en tijd """
from datetime import datetime, timedelta
import os
import hashlib
import requests
import icalendar
from dotenv import load_dotenv

load_dotenv()

def get_google_maps_url(place):
    """ Get google maps url """
    url_maps_place = 'https://maps.googleapis.com/maps/api/place/findplacefromtext/json?' + \
        'input=' + place + \
        f'&inputtype=textquery&fields=place_id&key={os.getenv("MAPS_API_KEY")}'
    response_place = requests.get(url_maps_place, timeout=10).json()['candidates'][0]['place_id']
    return 'https://www.google.com/maps/search/?api=1&query=Google&query_place_id='+ response_place

def get_google_maps_distance_and_duration(place):
    """ Get google maps distance """
    url_maps_distance = 'https://maps.googleapis.com/maps/api/distancematrix/json?' + \
        'units=metric&origins=51.4281731,5.3850569&destinations=' + \
        place + f'&key={os.getenv("MAPS_API_KEY")}'
    response = requests.get(url_maps_distance, timeout=10).json()
    return response['rows'][0]['elements'][0]['distance']['value'] / 1000, \
        response['rows'][0]['elements'][0]['duration']['value'] / 60

def get_sportlink_calendar():
    """ Get events from sportlink """
    url_sportlink = f'https://data.sportlink.com/ical-team?token={sportlink_token}'
    response = requests.get(url_sportlink, timeout=10)
    content = response.content
    return icalendar.Calendar.from_ical(content)

def get_events_from_calendar():
    """ Get events from calendar """
    events = []
    for event in calendar.walk('VEVENT'):
        summary = event.get('summary')
        start = event.get('dtstart').dt.strftime('%H:%M')
        end = event.get('dtend').dt.strftime('%H:%M')
        location = event.get('location')
        url_map = get_google_maps_url(location)
        location_link = f'[{location}]({url_map})'
        date = event.get('dtstart').dt.strftime('%Y-%m-%d')
        weekday = event.get('dtstart').dt.strftime('%A')
        if base_location in location:
            collection_time = (event.get('dtstart').dt - timebefore).strftime('%H:%M')
            distance_str = '0'
            duration_str = '0'
            costs = '€ 0'
        else:
            distance, duration = get_google_maps_distance_and_duration(location)

            # calculate colletion time: start - timebefore - time to travel - 5 min
            collection_time = \
                (event.get('dtstart').dt - timebefore \
                - timedelta(minutes=duration)).strftime('%H:%M')
            collection_time = collection_time[:-1] + '0'
            costs = f"€ {distance * travel_cost_per_km:.2f}"
            distance_str = f"{distance:.0f}"
            duration_str = f"{duration:.0f}"

        singleevent = [
            date, weekday, summary, collection_time, start, end, location_link,
            costs, distance_str, duration_str]
        events.append(singleevent)
    return events

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

def has_content_changed(directory, prefix, new_content):
    """ Check if file content has changed by finding old file with prefix """
    # Find the most recent old file matching the prefix
    old_file = find_old_file(directory, prefix, '.md')

    if not old_file:
        return True  # No old file found, so content has "changed"

    with open(old_file, 'r', encoding='utf-8') as file_old:
        old_content = file_old.read()
    return get_content_hash(old_content) != get_content_hash(new_content)

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
assert os.getenv('SPORTLINK_TOKEN'), 'SPORTLINK_TOKEN not set'
assert os.getenv('SPORTLINK_TEAM_LIST'), 'SPORTLINK_TEAM_LIST not set'

# Sportlink - combine token and list
sportlink_token = os.getenv('SPORTLINK_TOKEN')
sportlink_team_list = os.getenv('SPORTLINK_TEAM_LIST').split(',')

events_header_list = {
    'en': "| Date | Day | Summary | Time @<BASE> | Start | End | Location | Travel Costs " +  \
        "| Travel kms | Travel Minutes |\n",
    'nl': "| Datum | Dag | Samenvatting | Tijd @<BASE> | Start | Einde | Locatie | Reis kosten " + \
        "| Reis km | Reis minuten |\n"
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

for sportlink_team in sportlink_team_list:
    team_id = sportlink_team.split(':')[0]
    base_location = sportlink_team.split(':')[1]
    warming_up_time = float(sportlink_team.split(':')[2])
    travel_cost_per_km = float(sportlink_team.split(':')[3])
    team_email = sportlink_team.split(':')[4] if len(sportlink_team.split(':')) > 4 else ''
    print(f'\nProcessing {team_id} @ base: {base_location}')
    # Presence time before game
    timebefore = timedelta(minutes=warming_up_time)
    calendar = get_sportlink_calendar()
    calendar_events = get_events_from_calendar()
    # Sort events on date
    calendar_events.sort(key=lambda x: x[0])

    today = datetime.now().strftime("%Y-%m-%d")

    FILE_PATH_NL = f'docs/Rijschema_{team_id}_{today}.md'
    FILE_PATH_EN = f'docs/Drivingschedule_{team_id}_{today}.md'
    # Ensure the directories exist
    docs_dir = os.path.dirname(FILE_PATH_NL)
    os.makedirs(docs_dir, exist_ok=True)

    # Build content first to check if it changed
    CONTENT_EN = f'\n# Driving schedule {team_id}\n\n'
    CONTENT_EN += f'Base location: {base_location}\n\n'
    CONTENT_EN += f'Warming Up Time: {timebefore}\n\n'
    CONTENT_EN += f'Cost per km: €{travel_cost_per_km}\n\n'
    CONTENT_EN += get_events_header('en')
    CONTENT_EN += '| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n'
    for calendar_event in calendar_events:
        CONTENT_EN += '| ' + ' | '.join(calendar_event) + ' |\n'

    CONTENT_NL = f'\n# Rijschema {team_id}\n\n'
    CONTENT_NL += f'Basis locatie: {base_location}\n\n'
    CONTENT_NL += f'Warming Up Tijd: {timebefore}\n\n'
    CONTENT_NL += f'Kosten per km: €{travel_cost_per_km}\n\n'
    CONTENT_NL += get_events_header('nl')
    CONTENT_NL += '| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n'
    for calendar_event in calendar_events:
        calendar_event[1] = weekday_translation[calendar_event[1]]
        CONTENT_NL += '| ' + ' | '.join(calendar_event) + ' |\n'

    # Check if content changed by comparing with old files (if they exist)
    CHANGED_NL = has_content_changed(docs_dir, f'Rijschema_{team_id}', CONTENT_NL)
    CHANGED_EN = has_content_changed(docs_dir, f'Drivingschedule_{team_id}', CONTENT_EN)

    # Only create flag file if content changed (to trigger PDF conversion)
    if CHANGED_NL or CHANGED_EN:
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
