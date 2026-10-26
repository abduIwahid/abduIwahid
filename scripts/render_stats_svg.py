#!/usr/bin/env python3
"""Render stats.svg: streaks + totals from the public contributions graph
and the public REST profile (no API key needed)."""
import json, re, sys, urllib.request
from datetime import date, timedelta

USER = sys.argv[1] if len(sys.argv) > 1 else "abduIwahid"
OUT = sys.argv[2] if len(sys.argv) > 2 else "stats.svg"

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace")

def fetch_days(user):
    html = get(f"https://github.com/users/{user}/contributions")
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

def streaks(days):
    dates = sorted(days)
    longest = run = 0
    for d in dates:
        run = run + 1 if days[d] > 0 else 0
        longest = max(longest, run)
    cur, d = 0, date.fromisoformat(dates[-1])
    if days[dates[-1]] == 0:
        d -= timedelta(days=1)
    while days.get(d.isoformat(), 0) > 0:
        cur += 1
        d -= timedelta(days=1)
    return sum(days.values()), cur, longest

def main():
    days = fetch_days(USER)
    total, cur, longest = streaks(days)
    repos = stars = followers = 0
    since = ""
    try:
        u = json.loads(get(f"https://api.github.com/users/{USER}"))
        followers = u.get("followers", 0)
        since = date.fromisoformat(u["created_at"][:10]).strftime("%b %Y")
        rs = json.loads(get(f"https://api.github.com/users/{USER}/repos?per_page=100"))
        repos = len([r for r in rs if not r.get("fork")])
        stars = sum(r.get("stargazers_count", 0) for r in rs)
    except Exception as e:
        print("REST fallback:", e)
    F = "ui-monospace,'JetBrains Mono',Menlo,monospace"
    rows = [
        ("total contributions (1y)", f"{total}"),
        ("current streak", f"{cur} days"),
        ("longest streak", f"{longest} days"),
        ("public repos", f"{repos}"),
        ("total stars", f"{stars}"),
        ("followers", f"{followers}"),
        ("member since", since),
    ]
    H = 84 + len(rows) * 34 + 10
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="420" height="{H}" viewBox="0 0 420 {H}">',
           f'<rect width="420" height="{H}" rx="10" fill="#0D1117" stroke="#21262D"/>',
           '<circle cx="20" cy="20" r="5" fill="#FF5F57"/><circle cx="38" cy="20" r="5" fill="#FEBC2E"/><circle cx="56" cy="20" r="5" fill="#28C840"/>',
           f'<text x="74" y="25" font-family="{F}" font-size="12" fill="#7D8590">wadi@github: ~/stats</text>',
           f'<text x="24" y="66" font-family="{F}" font-size="30" font-weight="700" fill="#2FD08C">{cur}</text>',
           f'<text x="86" y="66" font-family="{F}" font-size="13" fill="#E6EDF3">day streak — still shipping</text>']
    y = 104
    for k, v in rows:
        out.append(f'<text x="24" y="{y}" font-family="{F}" font-size="12.5" fill="#7D8590">$ {k}</text>')
        out.append(f'<text x="396" y="{y}" text-anchor="end" font-family="{F}" font-size="12.5" font-weight="700" fill="#E6EDF3">{v}</text>')
        y += 34
    out.append("</svg>")
    open(OUT, "w").write("\n".join(out))
    print(f"wrote {OUT}: total={total} cur={cur} longest={longest} repos={repos} stars={stars}")

if __name__ == "__main__":
    main()
