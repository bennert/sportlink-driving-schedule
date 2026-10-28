import re


LOCATION_LINK_PATTERN = re.compile(r'^\[(.*)\]\(.*\)$')


def strip_travel_metrics(content):
    stripped_lines = []
    for line in content.splitlines(keepends=True):
        has_newline = line.endswith('\n')
        line_without_newline = line[:-1] if has_newline else line
        if line_without_newline.startswith('| ') and line_without_newline.endswith(' |'):
            cells = line_without_newline.split(' | ')
            if len(cells) in (8, 10):
                location_match = LOCATION_LINK_PATTERN.match(cells[6])
                if location_match:
                    cells[6] = location_match.group(1)
                if len(cells) == 10:
                    cells[8] = '<route metric>'
                    cells[9] = '<route metric> |'
                line_without_newline = ' | '.join(cells)
        stripped_lines.append(line_without_newline + ('\n' if has_newline else ''))
    return ''.join(stripped_lines)