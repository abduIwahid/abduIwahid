#!/usr/bin/env python3
"""Render contrib-heatmap.svg from the public GitHub contributions graph.
No API key needed: parses https://github.com/users/<user>/contributions.
Deep-green ramp on GitHub-dark, terminal style."""
import re, sys, urllib.request
from datetime import date, timedelta

USER = sys.argv[1] if len(sys.argv) > 1 else "abduIwahid"
OUT = sys.argv[2] if len(sys.argv) > 2 else "contrib-heatmap.svg"

def fetch_contributions(user):
    url = f"https://github.com/users/{user}/contributions"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    html = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace")
    return parse_days(html)

def parse_days(html):
    tips = {}
    for m in re.finditer(r'for="(contribution-day-component-[\d-]+)"[^>]*>([^<]+)', html):
        t = m.group(2).strip()
        if t.startswith("No contributions"):
            tips[m.group(1)] = 0
        else:
            mm = re.match(r"([\d,]+) contribution", t)
            tips[m.group(1)] = int(mm.group(1).replace(",", "")) if mm else 0
    days = {}
    for m in re.finditer(r'<td[^>]*class="ContributionCalendar-day"[^>]*>', html):
        tag = m.group(0)
        dt = re.search(r'data-date="(\d{4}-\d{2}-\d{2})"', tag)
        cid = re.search(r'id="(contribution-day-component-[\d-]+)"', tag)
        if dt and cid:
            days[dt.group(1)] = tips.get(cid.group(1), 0)
    return days

def main():
    days = fetch_contributions(USER)
    dates = sorted(days)
    first, last = date.fromisoformat(dates[0]), date.fromisoformat(dates[-1])
    start = first - timedelta(days=(first.weekday() + 1) % 7)  # back to Sunday
    weeks = ((last - start).days // 7) + 1
    LEVELS = ["#161B22", "#0B3B34", "#046A55", "#12936F", "#2FD08C"]
    def level(c):
        return 0 if c == 0 else 1 if c <= 2 else 2 if c <= 5 else 3 if c <= 9 else 4
    CELL, GAP, PAD_L, PAD_T = 12, 3, 34, 20
    W = PAD_L + weeks * (CELL + GAP) + 8
    H = PAD_T + 7 * (CELL + GAP) + 22
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
           f'<rect width="{W}" height="{H}" rx="8" fill="#0D1117"/>']
    # month labels
    seen_months = set()
    for w in range(weeks):
        d = start + timedelta(days=w * 7)
        key = (d.year, d.month)
        if key not in seen_months and not (w == 0 and d.day > 7):
            seen_months.add(key)
            x = PAD_L + w * (CELL + GAP)
            out.append(f'<text x="{x}" y="13" font-family="ui-monospace,Menlo,monospace" font-size="9" fill="#7D8590">{d.strftime("%b")}</text>')
    # weekday labels
    for r, lab in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        y = PAD_T + r * (CELL + GAP) + CELL - 2
        out.append(f'<text x="4" y="{y}" font-family="ui-monospace,Menlo,monospace" font-size="9" fill="#7D8590">{lab}</text>')
    # cells
    for w in range(weeks):
        for r in range(7):
            d = start + timedelta(days=w * 7 + r)
            if d < first or d > last:
                continue
            c = days.get(d.isoformat(), 0)
            x, y = PAD_L + w * (CELL + GAP), PAD_T + r * (CELL + GAP)
            out.append(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2.5" fill="{LEVELS[level(c)]}"><title>{c} contributions on {d.isoformat()}</title></rect>')
    # legend
    ly = PAD_T + 7 * (CELL + GAP) + 4
    out.append(f'<text x="{PAD_L}" y="{ly + 9}" font-family="ui-monospace,Menlo,monospace" font-size="9" fill="#7D8590">Less</text>')
    for i, col in enumerate(LEVELS):
        out.append(f'<rect x="{PAD_L + 30 + i * (CELL + GAP)}" y="{ly}" width="{CELL}" height="{CELL}" rx="2.5" fill="{col}"/>')
    out.append(f'<text x="{PAD_L + 36 + 5 * (CELL + GAP)}" y="{ly + 9}" font-family="ui-monospace,Menlo,monospace" font-size="9" fill="#7D8590">More</text>')
    total = sum(days.values())
    out.append(f'<text x="{W - 10}" y="{ly + 9}" text-anchor="end" font-family="ui-monospace,Menlo,monospace" font-size="9" fill="#7D8590">{total} contributions in the last year</text>')
    out.append("</svg>")
    open(OUT, "w").write("\n".join(out))
    print(f"wrote {OUT}: {weeks} weeks, total={total}")

if __name__ == "__main__":
    main()
