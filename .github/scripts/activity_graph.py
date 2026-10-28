"""Generate a graph from GitHub's public contribution calendar (stdlib only)."""
from datetime import date, timedelta
from html import escape
from html.parser import HTMLParser
from pathlib import Path
import re
import urllib.request


class Calendar(HTMLParser):
    def __init__(self):
        super().__init__()
        self.dates, self.counts = {}, {}
        self.target = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'td' and 'data-date' in attrs:
            self.dates[attrs['id']] = attrs['data-date']
        if tag == 'tool-tip':
            self.target = attrs.get('for')

    def handle_data(self, text):
        if self.target and 'contribution' in text:
            match = re.match(r'\s*([\d,]+|No) contributions? on ', text)
            if match:
                self.counts[self.target] = 0 if match[1] == 'No' else int(match[1].replace(',', ''))

    def handle_endtag(self, tag):
        if tag == 'tool-tip':
            self.target = None


def generate(source):
    calendar = Calendar()
    calendar.feed(source)
    days = sorted((day, calendar.counts[key]) for key, day in calendar.dates.items() if key in calendar.counts)
    if len(days) < 31:
        raise ValueError('GitHub calendar is incomplete; keeping the previous graph')
    days = days[-31:]
    if any(date.fromisoformat(b[0]) - date.fromisoformat(a[0]) != timedelta(days=1) for a, b in zip(days, days[1:])):
        raise ValueError('Contribution calendar has missing dates')
    ceiling = max(4, max(count for _, count in days))
    points = [(55 + i * 29, 245 - count / ceiling * 175) for i, (_, count) in enumerate(days)]
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 980 310" role="img" aria-labelledby="title desc">',
           '<title id="title">Abner’s GitHub activity graph</title>',
           f'<desc id="desc">Daily contributions from {days[0][0]} to {days[-1][0]}</desc>',
           '<rect width="980" height="310" rx="8" fill="#0d1117"/>',
           '<g font-family="sans-serif" fill="#c9d1d9">',
           '<text x="40" y="35" font-size="20">Abner’s GitHub Activity — Last 31 Days</text>']
    for i in range(5):
        y = 245 - i * 175 / 4
        svg += [f'<path d="M55 {y}H925" stroke="#21262d"/>', f'<text x="45" y="{y+4}" text-anchor="end" font-size="11">{ceiling*i/4:g}</text>']
    coords = ' '.join(f'{x:.2f},{y:.2f}' for x, y in points)
    svg += [f'<polygon points="55,245 {coords} 925,245" fill="#238636" opacity="0.18"/>', f'<polyline points="{coords}" fill="none" stroke="#39d353" stroke-width="2"/>']
    for i, ((day, count), (x, y)) in enumerate(zip(days, points)):
        svg.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="3" fill="#39d353"><title>{escape(day)}: {count} contributions</title></circle>')
        if i % 5 == 0:
            svg.append(f'<text x="{x}" y="268" text-anchor="middle" font-size="11">{day[5:]}</text>')
    svg += [f'<text x="925" y="294" text-anchor="end" font-size="11">Source: GitHub public contributions · Updated {days[-1][0]}</text>', '</g></svg>']
    return '\n'.join(svg) + '\n'


if __name__ == '__main__':
    request = urllib.request.Request('https://github.com/users/abner-forever/contributions', headers={'User-Agent': 'abner-profile-activity-graph'})
    with urllib.request.urlopen(request, timeout=60) as response:
        svg = generate(response.read().decode('utf-8'))
    target = Path('assets/activity-graph.svg')
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(svg, encoding='utf-8')
