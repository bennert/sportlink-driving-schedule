import hashlib
import html
import re
import shutil
from datetime import date
from pathlib import Path


SCHEDULE_PDF_PATTERN = re.compile(r'^Rijschema_(.+)_(\d{4}-\d{2}-\d{2})\.pdf$')


def team_slug(team_id):
    readable_slug = re.sub(r'[^a-z0-9]+', '-', team_id.casefold()).strip('-') or 'team'
    stable_suffix = hashlib.sha256(team_id.encode('utf-8')).hexdigest()[:8]
    return f'{readable_slug}-{stable_suffix}'


def publish_latest_schedules(source_directories, output_directory):
    latest_by_team = {}
    for source_directory in source_directories:
        for pdf_path in sorted(Path(source_directory).glob('Rijschema_*.pdf')):
            match = SCHEDULE_PDF_PATTERN.fullmatch(pdf_path.name)
            if not match:
                continue
            team_id, date_text = match.groups()
            schedule_date = date.fromisoformat(date_text)
            current = latest_by_team.get(team_id)
            if current is None or schedule_date > current[0]:
                latest_by_team[team_id] = (schedule_date, pdf_path)

    if not latest_by_team:
        raise FileNotFoundError('No generated Dutch driving schedule PDFs were found.')

    output_path = Path(output_directory)
    team_output_path = output_path / 'teams'
    if team_output_path.exists():
        shutil.rmtree(team_output_path)
    team_output_path.mkdir(parents=True, exist_ok=True)

    entries = []
    for team_id, (schedule_date, pdf_path) in sorted(latest_by_team.items()):
        filename = f'{team_slug(team_id)}.pdf'
        shutil.copyfile(pdf_path, team_output_path / filename)
        escaped_team_id = html.escape(team_id)
        entries.append(
            f'<li><h2>{escaped_team_id}</h2>'
            f'<p>Schema bijgewerkt: {schedule_date.strftime("%d-%m-%Y")}</p>'
            f'<a href="teams/{filename}">Bekijk rijschema als PDF</a></li>'
        )

    index_html = '''<!doctype html>
<html lang="nl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Actuele rijschema's</title>
  <style>
    body { color: #202a35; font: 16px/1.5 sans-serif; margin: 2rem auto; max-width: 46rem; padding: 0 1rem; }
    h1 { font-size: 1.8rem; }
    h2 { font-size: 1.2rem; margin-bottom: 0; }
    ul { list-style: none; padding: 0; }
    li { border-bottom: 1px solid #d5dbe0; padding: 1rem 0; }
    p { color: #586574; margin: 0.25rem 0; }
  </style>
</head>
<body>
  <main>
    <h1>Actuele rijschema's</h1>
    <ul>
      ''' + '\n      '.join(entries) + '''
    </ul>
  </main>
</body>
</html>
'''
    output_path.mkdir(parents=True, exist_ok=True)
    (output_path / 'index.html').write_text(index_html, encoding='utf-8')
    print(f'Published {len(entries)} team schedule link(s) to {output_path}')
    return latest_by_team


if __name__ == '__main__':
    publish_latest_schedules(('docs',), 'site')
